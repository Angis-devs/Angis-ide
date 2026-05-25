import struct


class Buffer:
    def __init__(self, size_or_data: int | bytes | bytearray | str = 0):
        if isinstance(size_or_data, int):
            self._data = bytearray(max(0, size_or_data))
        elif isinstance(size_or_data, (bytes, bytearray)):
            self._data = bytearray(size_or_data)
        elif isinstance(size_or_data, str):
            self._data = bytearray(size_or_data, "utf-8")
        else:
            raise TypeError(f"Buffer expects int, bytes, or str, got {type(size_or_data)}")

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"Buffer({len(self._data)} bytes)"

    def read(self, offset: int, length: int) -> bytes:
        return bytes(self._data[offset : offset + length])

    def write(self, offset: int, data: object) -> None:
        if isinstance(data, str):
            raw = data.encode("utf-8")
        elif isinstance(data, Buffer):
            raw = bytes(data._data)
        elif isinstance(data, int):
            raw = bytes([data & 0xFF])
        elif isinstance(data, bytes):
            raw = data
        elif isinstance(data, bytearray):
            raw = bytes(data)
        else:
            raise TypeError(f"Buffer.write expects str, int, or bytes, got {type(data)}")
        self._data[offset : offset + len(raw)] = raw

    def read_int8(self, offset: int) -> int:
        return struct.unpack_from("b", self._data, offset)[0]

    def read_uint8(self, offset: int) -> int:
        return struct.unpack_from("B", self._data, offset)[0]

    def read_int16(self, offset: int, little_endian: bool = True) -> int:
        return struct.unpack_from("<h" if little_endian else ">h", self._data, offset)[0]

    def read_uint16(self, offset: int, little_endian: bool = True) -> int:
        return struct.unpack_from("<H" if little_endian else ">H", self._data, offset)[0]

    def read_int32(self, offset: int, little_endian: bool = True) -> int:
        return struct.unpack_from("<i" if little_endian else ">i", self._data, offset)[0]

    def read_uint32(self, offset: int, little_endian: bool = True) -> int:
        return struct.unpack_from("<I" if little_endian else ">I", self._data, offset)[0]

    def read_int64(self, offset: int, little_endian: bool = True) -> int:
        return struct.unpack_from("<q" if little_endian else ">q", self._data, offset)[0]

    def read_float32(self, offset: int, little_endian: bool = True) -> float:
        return struct.unpack_from("<f" if little_endian else ">f", self._data, offset)[0]

    def read_float64(self, offset: int, little_endian: bool = True) -> float:
        return struct.unpack_from("<d" if little_endian else ">d", self._data, offset)[0]

    def write_int8(self, offset: int, value: int) -> None:
        struct.pack_into("b", self._data, offset, value)

    def write_uint8(self, offset: int, value: int) -> None:
        struct.pack_into("B", self._data, offset, value)

    def write_int16(self, offset: int, value: int, little_endian: bool = True) -> None:
        struct.pack_into("<h" if little_endian else ">h", self._data, offset, value)

    def write_uint16(self, offset: int, value: int, little_endian: bool = True) -> None:
        struct.pack_into("<H" if little_endian else ">H", self._data, offset, value)

    def write_int32(self, offset: int, value: int, little_endian: bool = True) -> None:
        struct.pack_into("<i" if little_endian else ">i", self._data, offset, value)

    def write_uint32(self, offset: int, value: int, little_endian: bool = True) -> None:
        struct.pack_into("<I" if little_endian else ">I", self._data, offset, value)

    def write_int64(self, offset: int, value: int, little_endian: bool = True) -> None:
        struct.pack_into("<q" if little_endian else ">q", self._data, offset, value)

    def write_float32(self, offset: int, value: float, little_endian: bool = True) -> None:
        struct.pack_into("<f" if little_endian else ">f", self._data, offset, value)

    def write_float64(self, offset: int, value: float, little_endian: bool = True) -> None:
        struct.pack_into("<d" if little_endian else ">d", self._data, offset, value)

    def to_bytes(self) -> bytes:
        return bytes(self._data)

    def hex(self) -> str:
        return self._data.hex()

    def fill(self, value: int = 0) -> None:
        self._data[:] = bytes([value & 0xFF]) * len(self._data)

    @staticmethod
    def from_hex(text: str) -> "Buffer":
        return Buffer(bytes.fromhex(text.strip()))

    @staticmethod
    def from_bytes(data: bytes | bytearray) -> "Buffer":
        return Buffer(data)

    def as_bytearray(self) -> bytearray:
        return self._data

    def __bytes__(self) -> bytes:
        return bytes(self._data)

    @staticmethod
    def copy_of(other: "Buffer", start: int = 0, length: int | None = None) -> "Buffer":
        data = other._data[start:]
        if length is not None:
            data = data[:length]
        return Buffer(bytes(data))
