import csv
import io
from typing import Mapping


__all__ = ["CSVRenderer"]


class CSVRenderer:
    """Render view result to CSV.

    Views using this renderer must return a sequence of dict-like items.

    """

    def __call__(self, info):
        def _render(value: Mapping, system) -> str:
            request = system.get("request")
            if request is not None:
                response = request.response
                content_type = response.content_type
                if content_type == response.default_content_type:
                    response.content_type = "text/csv"
            rows = iter(value)
            first_row = next(rows, None)
            if first_row is None:
                return ""
            file = io.StringIO()
            fields = tuple(first_row.keys())
            header = {f: " ".join(f.split("_")).capitalize() for f in fields}
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writerow(header)
            writer.writerow(first_row)
            writer.writerows(rows)
            return file.getvalue()

        return _render
