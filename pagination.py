from typing import List

def paginate(data: List[str], page: int, page_size: int) -> List[str]:
    start = (page - 1) * page_size
    end = start + page_size
    return data[start:end]
