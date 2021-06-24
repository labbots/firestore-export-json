import array
import logging
import os
import struct

import google_crc32c

# Data format is defined @ https://github.com/google/leveldb/blob/master/doc/log_format.md

ENDIANNESS = "little"

CRC_INIT = 0

BLOCK_SIZE = 32 * 1024

HEADER_FORMAT = "<IHB"

HEADER_LENGTH = struct.calcsize(HEADER_FORMAT)

# the type is the "B" part of the HEADER_FORMAT
RECORD_TYPE_LENGTH = struct.calcsize("<B")

RECORD_TYPE_NONE = 0

RECORD_TYPE_FULL = 1

RECORD_TYPE_FIRST = 2

RECORD_TYPE_MIDDLE = 3

RECORD_TYPE_LAST = 4


class Error(Exception):
    """Base class for exceptions in this module."""


class InvalidRecordError(Error):
    """Raised when invalid record encountered."""


class FileReader(object):
    """Interface specification for writers to be used with recordrecords module.

    FileReader defines a reader with position and efficient seek/position
    determining. All reads occur at current position.
    """

    def read(self, size):
        """Read data from file.

        Reads data from current position and advances position past the read data
        block.
        Args:
          size: number of bytes to read.
        Returns:
          iterable over bytes. If number of bytes read is less then 'size' argument,
          it is assumed that end of file was reached.
        """
        raise NotImplementedError()

    def tell(self):
        """Get current file position.

        Returns:
          current position as a byte offset in the file as integer.
        """
        raise NotImplementedError()


_CRC_MASK_DELTA = 0xA282EAD8


def _unmask_crc(masked_crc):
    """Unmask crc.

    Args:
      masked_crc: masked integer crc.
    Retruns:
      orignal crc.
    """
    rot = (masked_crc - _CRC_MASK_DELTA) & 0xFFFFFFFF
    return ((rot >> 17) | (rot << 15)) & 0xFFFFFFFF


class RecordsReader(object):
    """A reader for records format."""

    def __init__(self, reader, no_check_crc=True):
        self.__reader = reader
        self.no_check_crc = no_check_crc

    def __try_read_record(self):
        """Try reading a record.

        Returns:
          (data, record_type) tuple.
        Raises:
          EOFError: when end of file was reached.
          InvalidRecordError: when valid record could not be read.
        """
        block_remaining = BLOCK_SIZE - self.__reader.tell() % BLOCK_SIZE
        if block_remaining < HEADER_LENGTH:
            return ("", RECORD_TYPE_NONE)

        header = self.__reader.read(HEADER_LENGTH)
        if len(header) != HEADER_LENGTH:
            raise EOFError("Read %s bytes instead of %s" % (len(header), HEADER_LENGTH))

        (masked_crc, length, record_type) = struct.unpack(HEADER_FORMAT, header)

        if length + HEADER_LENGTH > block_remaining:
            raise InvalidRecordError("Length is too big")

        data = self.__reader.read(length)
        if len(data) != length:
            raise EOFError(
                "Not enough data read. Expected: %s but got %s" % (length, len(data))
            )

        if record_type == RECORD_TYPE_NONE:
            return ("", record_type)

        if not self.no_check_crc:
            actual_crc = google_crc32c.value(
                record_type.to_bytes(RECORD_TYPE_LENGTH, ENDIANNESS) + data
            )
            if actual_crc != _unmask_crc(masked_crc):
                raise InvalidRecordError("Data crc does not match")
        return (data, record_type)

    def __sync(self):
        """Skip reader to the block boundary."""
        pad_length = BLOCK_SIZE - self.__reader.tell() % BLOCK_SIZE
        if pad_length and pad_length != BLOCK_SIZE:
            data = self.__reader.read(pad_length)
            if len(data) != pad_length:
                raise EOFError("Read %d bytes instead of %d" % (len(data), pad_length))

    def read(self):
        """Reads record from current position in reader."""
        data = None
        while True:
            last_offset = self.tell()
            try:
                (chunk, record_type) = self.__try_read_record()
                if record_type == RECORD_TYPE_NONE:
                    self.__sync()
                elif record_type == RECORD_TYPE_FULL:
                    if data is not None:
                        logging.warning(
                            "Ordering corruption: Got FULL record while already "
                            "in a chunk at offset %d",
                            last_offset,
                        )
                    return chunk
                elif record_type == RECORD_TYPE_FIRST:
                    if data is not None:
                        logging.warning(
                            "Ordering corruption: Got FIRST record while already "
                            "in a chunk at offset %d",
                            last_offset,
                        )
                    data = chunk
                elif record_type == RECORD_TYPE_MIDDLE:
                    if data is None:
                        logging.warning(
                            "Ordering corruption: Got MIDDLE record before FIRST "
                            "record at offset %d",
                            last_offset,
                        )
                    else:
                        data += chunk
                elif record_type == RECORD_TYPE_LAST:
                    if data is None:
                        logging.warning(
                            "Ordering corruption: Got LAST record but no chunk is in "
                            "progress at offset %d",
                            last_offset,
                        )
                    else:
                        result = data + chunk
                        data = None
                        return result
                else:
                    raise InvalidRecordError(
                        "Unsupported record type: %s" % record_type
                    )

            except InvalidRecordError:
                logging.warning(
                    "Invalid record encountered at %s. Syncing to " "the next block",
                    last_offset,
                )
                data = None
                self.__sync()

    def __iter__(self):
        """Iterate through records."""
        try:
            while True:
                yield self.read()
        except EOFError:
            pass

    def tell(self):
        """Return file's current position."""
        return self.__reader.tell()
