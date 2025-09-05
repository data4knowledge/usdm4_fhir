import re
from simple_error_log.errors import Errors


def errors_clean_all(errors: Errors) -> list[dict]:
    result = errors.to_dict(0)
    for item in result:
        item = _fix_timestamp(item)
        item = _remove_file_paths(item)
    print(f"RESULT: {result}")
    return result


def error_clean(errors: Errors, index=0) -> dict:
    result = errors._items[index].to_dict()
    result = _remove_file_paths(result)
    return _fix_timestamp(result)


def _fix_timestamp(data: dict) -> dict:
    timestamp_pattern = r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})\.(\d{6})"
    if "timestamp" in data:
        data["timestamp"] = re.sub(
            timestamp_pattern, "YYYY-MM-DD HH:MM:SS.nnnnnn", data["timestamp"]
        )
    return data


def _clean_traceback_paths(error_text: str) -> str:
    # Pattern to match 'File "path"' in traceback
    file_pattern = r'File\s+"([^"]+)"'

    def clean_path(match):
        full_path = match.group(1)
        # Find the position of 'src/usdm4' in the path
        src_index = full_path.find("src/usdm4")
        if src_index != -1:
            # Keep only the part from 'src/usdm4' onwards
            cleaned_path = full_path[src_index:]
            return f'File "{cleaned_path}"'
        else:
            parts = full_path.split("site-packages/")
            print(f"PARTS: {parts}")
            if len(parts) >= 2:
                return parts[-1]
            # If 'src/usdm4' not found, return original
            return full_path

    # Replace all file paths in the error text
    cleaned_text = re.sub(file_pattern, clean_path, error_text)
    return cleaned_text


def _remove_file_paths(data: dict) -> dict:
    if "message" in data:
        data["message"] = _clean_traceback_paths(data["message"])
    return data
