from dog_connection_config import DOA_ENABLED


def get_doa_degrees():
    if not DOA_ENABLED:
        return None

    # Future integration point:
    # return the speaker direction in degrees, relative to the board/mic array.
    return None
