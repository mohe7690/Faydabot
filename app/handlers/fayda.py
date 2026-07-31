"""
Fayda self-service verification client.

IMPORTANT: This is a STUB. Replace the two methods below with calls to whatever
official/authorized self-service mechanism you're using to (a) trigger an OTP
to the phone number registered against a FAN, and (b) confirm the OTP and
fetch the ID holder's own record.

Do not implement anything here that looks up a FAN and returns data WITHOUT
first requiring a successful OTP confirmation tied to that same FAN. The OTP
step is what proves the requester is the ID owner - don't let callers skip it.
"""

import random
import string
from dataclasses import dataclass

import httpx

from app.config import settings


class FaydaVerificationError(Exception):
    pass


@dataclass
class FaydaProfile:
    fan: str
    full_name: str
    date_of_birth: str
    photo_url: str | None
    # Extend with whatever fields the real record exposes.


class FaydaClient:
    def __init__(self) -> None:
        self._base_url = settings.fayda_verify_base_url
        self._api_key = settings.fayda_api_key

    async def send_otp(self, fan: str) -> str:
        """
        Trigger an OTP to the phone registered to `fan`.
        Returns an opaque `otp_session_id` to pass into confirm_otp().

        STUBBED: generates a fake session id and does not actually send anything.
        Wire this to the real endpoint before going live.
        """
        if not self._base_url:
            # Dev/mock mode - no real endpoint configured yet.
            return "mock-session-" + "".join(random.choices(string.digits, k=6))

        async with httpx.AsyncClient(base_url=self._base_url, timeout=15) as client:
            resp = await client.post(
                "/otp/send",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"fan": fan},
            )
            resp.raise_for_status()
            return resp.json()["session_id"]

    async def confirm_otp(self, session_id: str, otp_code: str) -> FaydaProfile:
        """
        Confirm the OTP and, on success, return the ID holder's own profile.
        Raises FaydaVerificationError on wrong/expired OTP.

        STUBBED: accepts "1234" as a fake valid code for local dev only.
        """
        if session_id.startswith("mock-session-"):
            if otp_code != "1234":
                raise FaydaVerificationError("Invalid OTP (dev mode: use 1234)")
            return FaydaProfile(
                fan="MOCK-0000-0000",
                full_name="Test User",
                date_of_birth="2000-01-01",
                photo_url=None,
            )

        async with httpx.AsyncClient(base_url=self._base_url, timeout=15) as client:
            resp = await client.post(
                "/otp/confirm",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"session_id": session_id, "otp_code": otp_code},
            )
            if resp.status_code == 401:
                raise FaydaVerificationError("Invalid or expired OTP")
            resp.raise_for_status()
            data = resp.json()
            return FaydaProfile(
                fan=data["fan"],
                full_name=data["full_name"],
                date_of_birth=data["date_of_birth"],
                photo_url=data.get("photo_url"),
            )


fayda_client = FaydaClient()
