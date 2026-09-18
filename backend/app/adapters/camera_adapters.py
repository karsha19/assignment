"""
Camera source adapter abstraction.

Every adapter exposes the same interface (source identification, connection
status, stream metadata, playback/stream reference, health information)
regardless of the underlying transport. Today only RecordedVideoAdapter and
SimulatedCameraAdapter are functional. RTSPAdapter, ONVIFAdapter and
VendorAPIAdapter are documented stubs that define the contract a future
implementation must fulfil -- they intentionally raise NotImplementedError
so the system never silently pretends to have a live connection it does not
have.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class StreamInfo:
    source_type: str
    is_connected: bool
    playback_reference: Optional[str]
    label: str


class CameraSourceAdapter(ABC):
    def __init__(self, camera_code: str, stream_reference: Optional[str]):
        self.camera_code = camera_code
        self.stream_reference = stream_reference

    @abstractmethod
    def get_stream_info(self) -> StreamInfo:
        ...

    @abstractmethod
    def check_health(self) -> bool:
        """Returns True if the source is currently considered reachable."""
        ...


class RecordedVideoAdapter(CameraSourceAdapter):
    """Serves a pre-recorded MP4 file as the camera's 'feed'. This is NOT a
    live stream and the UI must label it as recorded footage."""

    def get_stream_info(self) -> StreamInfo:
        return StreamInfo(
            source_type="recorded",
            is_connected=bool(self.stream_reference),
            playback_reference=self.stream_reference,
            label="Recorded MP4 (sample footage)",
        )

    def check_health(self) -> bool:
        return bool(self.stream_reference)


class SimulatedCameraAdapter(CameraSourceAdapter):
    """Represents a camera with no real video, used purely to demonstrate
    registry/health/analytics workflows without a video file."""

    def get_stream_info(self) -> StreamInfo:
        return StreamInfo(
            source_type="simulated",
            is_connected=True,
            playback_reference=None,
            label="Simulated source (no video attached)",
        )

    def check_health(self) -> bool:
        return True


class RTSPAdapter(CameraSourceAdapter):
    """Future integration point. A production implementation would open an
    RTSP session (e.g. via GStreamer/ffmpeg) and relay to WebRTC/HLS for
    browser playback."""

    def get_stream_info(self) -> StreamInfo:
        raise NotImplementedError("RTSP integration is not implemented in this prototype")

    def check_health(self) -> bool:
        raise NotImplementedError("RTSP integration is not implemented in this prototype")


class ONVIFAdapter(CameraSourceAdapter):
    """Future integration point for ONVIF discovery/profile negotiation."""

    def get_stream_info(self) -> StreamInfo:
        raise NotImplementedError("ONVIF integration is not implemented in this prototype")

    def check_health(self) -> bool:
        raise NotImplementedError("ONVIF integration is not implemented in this prototype")


class VendorAPIAdapter(CameraSourceAdapter):
    """Future integration point for vendor-specific SDK/API-based cameras."""

    def get_stream_info(self) -> StreamInfo:
        raise NotImplementedError("Vendor API integration is not implemented in this prototype")

    def check_health(self) -> bool:
        raise NotImplementedError("Vendor API integration is not implemented in this prototype")


_ADAPTER_MAP = {
    "recorded": RecordedVideoAdapter,
    "simulated": SimulatedCameraAdapter,
    "rtsp": RTSPAdapter,
    "onvif": ONVIFAdapter,
    "vendor_api": VendorAPIAdapter,
}


def get_adapter(source_protocol: str, camera_code: str, stream_reference: Optional[str]) -> CameraSourceAdapter:
    adapter_cls = _ADAPTER_MAP.get(source_protocol, SimulatedCameraAdapter)
    return adapter_cls(camera_code, stream_reference)
