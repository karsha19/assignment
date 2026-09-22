
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
        ...


class RecordedVideoAdapter(CameraSourceAdapter):

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

    def get_stream_info(self) -> StreamInfo:
        raise NotImplementedError("RTSP integration is not implemented in this prototype")

    def check_health(self) -> bool:
        raise NotImplementedError("RTSP integration is not implemented in this prototype")


class ONVIFAdapter(CameraSourceAdapter):

    def get_stream_info(self) -> StreamInfo:
        raise NotImplementedError("ONVIF integration is not implemented in this prototype")

    def check_health(self) -> bool:
        raise NotImplementedError("ONVIF integration is not implemented in this prototype")


class VendorAPIAdapter(CameraSourceAdapter):

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
