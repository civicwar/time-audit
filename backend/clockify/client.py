import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from backend.settings import (
    CLOCKIFY_API_BASE_URL,
    CLOCKIFY_REPORTS_BASE_URL,
    CLOCKIFY_WORKSPACE_ID,
    require_clockify_api_key,
)


class ClockifyConfigurationError(RuntimeError):
    pass


class ClockifyClientError(RuntimeError):
    pass


class ClockifyHttpError(ClockifyClientError):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"Clockify request failed: {detail}")
        self.status_code = status_code
        self.detail = detail


@dataclass(frozen=True)
class ClockifyProfile:
    workspace_id: str
    workspace_name: str | None
    user_id: str | None
    user_name: str | None
    default_timezone: str | None


class ClockifyClient:
    def __init__(self) -> None:
        try:
            self._api_key = require_clockify_api_key()
        except RuntimeError as exc:
            raise ClockifyConfigurationError(str(exc)) from exc
        self._api_base_url = CLOCKIFY_API_BASE_URL.rstrip("/")
        self._reports_base_url = CLOCKIFY_REPORTS_BASE_URL.rstrip("/")
        self._workspace_id_override = CLOCKIFY_WORKSPACE_ID

    async def get_profile(self) -> ClockifyProfile:
        async with self._get_client() as client:
            user = await self._request_json(client, "GET", f"{self._api_base_url}/user")
            workspace_id = self._workspace_id_override or user.get("activeWorkspace") or user.get("defaultWorkspace")
            if not workspace_id:
                raise ClockifyClientError("Could not determine the active Clockify workspace for this API key.")

            workspace_name = None
            try:
                workspace = await self._request_json(client, "GET", f"{self._api_base_url}/workspaces/{workspace_id}")
                workspace_name = workspace.get("name")
            except ClockifyClientError:
                workspace_name = None

            settings = user.get("settings") or {}
            return ClockifyProfile(
                workspace_id=workspace_id,
                workspace_name=workspace_name,
                user_id=user.get("id"),
                user_name=user.get("name"),
                default_timezone=settings.get("timeZone"),
            )

    async def fetch_detailed_report_csv(
        self,
        *,
        start_date: date,
        end_date: date,
        timezone_name: str,
    ) -> str:
        if end_date < start_date:
            raise ClockifyClientError("End date must be on or after start date.")

        tzinfo = self._get_timezone(timezone_name)
        profile = await self.get_profile()
        user_map = await self._fetch_workspace_users(profile.workspace_id)
        start_utc, end_utc = self._date_range_to_utc(start_date, end_date, tzinfo)

        rows: list[dict[str, Any]] = []
        page = 1
        page_size = 200
        async with self._get_client() as client:
            try:
                while True:
                    payload = {
                        "dateRangeStart": self._format_utc(start_utc),
                        "dateRangeEnd": self._format_utc(end_utc),
                        "dateRangeType": "ABSOLUTE",
                        "exportType": "JSON",
                        "timeZone": timezone_name,
                        "userLocale": "en",
                        "sortOrder": "ASCENDING",
                        "detailedFilter": {
                            "page": page,
                            "pageSize": page_size,
                            "sortColumn": "ID",
                        },
                    }
                    data = await self._request_json(
                        client,
                        "POST",
                        f"{self._reports_base_url}/workspaces/{profile.workspace_id}/reports/detailed",
                        json=payload,
                    )
                    page_entries = self._extract_entries(data)
                    rows.extend(self._entries_to_rows(page_entries, user_map, tzinfo))
                    if len(page_entries) < page_size:
                        break
                    page += 1
            except ClockifyHttpError as exc:
                if exc.status_code != 403:
                    raise
                fallback_entries = await self._fetch_workspace_time_entries(
                    workspace_id=profile.workspace_id,
                    start_utc=start_utc,
                    end_utc=end_utc,
                    fallback_user_id=profile.user_id,
                )
                rows = self._entries_to_rows(fallback_entries, user_map, tzinfo)

        if not rows:
            raise ClockifyClientError("Clockify returned no time entries for the selected date range.")

        return self._rows_to_csv(rows)

    async def _fetch_workspace_time_entries(
        self,
        *,
        workspace_id: str,
        start_utc: datetime,
        end_utc: datetime,
        fallback_user_id: str | None,
    ) -> list[dict[str, Any]]:
        user_map = await self._fetch_workspace_users(workspace_id)
        user_ids = list(user_map)
        if fallback_user_id and fallback_user_id not in user_map:
            user_ids.append(fallback_user_id)

        entries: list[dict[str, Any]] = []
        async with self._get_client() as client:
            for user_id in user_ids:
                page = 1
                page_size = 200
                while True:
                    response = await client.get(
                        f"{self._api_base_url}/workspaces/{workspace_id}/user/{user_id}/time-entries",
                        params={
                            "start": self._format_utc(start_utc),
                            "end": self._format_utc(end_utc),
                            "page": page,
                            "page-size": page_size,
                        },
                    )
                    data = self._parse_json_response(response)
                    if not isinstance(data, list):
                        raise ClockifyClientError("Clockify returned an unexpected time-entry response format.")

                    entries.extend(data)
                    if len(data) < page_size:
                        break
                    page += 1

        return entries

    async def _fetch_workspace_users(self, workspace_id: str) -> dict[str, str]:
        users: dict[str, str] = {}
        page = 1
        page_size = 200
        async with self._get_client() as client:
            while True:
                response = await client.get(
                    f"{self._api_base_url}/workspaces/{workspace_id}/users",
                    params={"page": page, "page-size": page_size},
                )
                data = self._parse_json_response(response)
                for user in data:
                    user_id = user.get("id")
                    user_name = user.get("name") or user.get("email")
                    if user_id and user_name:
                        users[user_id] = user_name

                if response.headers.get("Last-Page", "true").lower() == "true" or len(data) < page_size:
                    break
                page += 1
        return users

    @staticmethod
    def _extract_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("timeentries", "timeEntries", "time_entries"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        raise ClockifyClientError("Clockify detailed report response did not include time entries.")

    @staticmethod
    def _rows_to_csv(rows: list[dict[str, Any]]) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "User",
                "Description",
                "Start Date",
                "Start Time",
                "End Date",
                "End Time",
                "Duration (decimal)",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def _entries_to_rows(
        self,
        entries: list[dict[str, Any]],
        user_map: dict[str, str],
        tzinfo: ZoneInfo,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for entry in entries:
            interval = entry.get("timeInterval") or {}
            start_raw = interval.get("start")
            end_raw = interval.get("end")
            if not start_raw or not end_raw:
                continue

            start_dt = self._parse_datetime(start_raw).astimezone(tzinfo)
            end_dt = self._parse_datetime(end_raw).astimezone(tzinfo)
            duration_hours = round((end_dt - start_dt).total_seconds() / 3600, 6)
            if duration_hours < 0:
                continue

            user_name = (
                entry.get("userName")
                or (entry.get("user") or {}).get("name")
                or user_map.get(entry.get("userId", ""))
                or "Unknown User"
            )
            rows.append(
                {
                    "User": user_name,
                    "Description": entry.get("description") or "",
                    "Start Date": start_dt.strftime("%d/%m/%Y"),
                    "Start Time": start_dt.strftime("%H:%M:%S"),
                    "End Date": end_dt.strftime("%d/%m/%Y"),
                    "End Time": end_dt.strftime("%H:%M:%S"),
                    "Duration (decimal)": duration_hours,
                }
            )
        return rows

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _format_utc(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    @staticmethod
    def _date_range_to_utc(start_date: date, end_date: date, tzinfo: ZoneInfo) -> tuple[datetime, datetime]:
        start_local = datetime.combine(start_date, time.min, tzinfo=tzinfo)
        end_local = datetime.combine(end_date, time.max, tzinfo=tzinfo)
        return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

    @staticmethod
    def _get_timezone(timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ClockifyClientError(f"Unsupported timezone: {timezone_name}") from exc

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=20.0),
            headers={
                "X-Api-Key": self._api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    async def _request_json(self, client: httpx.AsyncClient, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        response = await client.request(method, url, **kwargs)
        data = self._parse_json_response(response)
        if not isinstance(data, dict):
            raise ClockifyClientError("Clockify returned an unexpected response format.")
        return data

    @staticmethod
    def _parse_json_response(response: httpx.Response) -> Any:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text.strip() or str(exc)
            raise ClockifyHttpError(response.status_code, detail) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise ClockifyClientError("Clockify returned a non-JSON response.") from exc