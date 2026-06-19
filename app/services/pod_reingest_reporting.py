import csv
import os


class PodReingestReporter:
    """Write CSV reports for POD re-ingestion runs.

    - `full_report_path` captures all processed rows and statuses.
    - `failed_report_path` captures only failed rows for manual remediation.
    """

    FULL_FIELDS = [
        "id",
        "consignment_number",
        "old_pod_image",
        "new_pod_image",
        "status",
        "error",
    ]

    FAILED_FIELDS = [
        "id",
        "consignment_number",
        "url",
        "error",
    ]

    def __init__(self, full_report_path, failed_report_path):
        self.full_report_path = full_report_path
        self.failed_report_path = failed_report_path

        os.makedirs(os.path.dirname(full_report_path) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(failed_report_path) or ".", exist_ok=True)

        self._full_file = open(full_report_path, "w", newline="", encoding="utf-8")
        self._failed_file = open(failed_report_path, "w", newline="", encoding="utf-8")

        self._full_writer = csv.DictWriter(self._full_file, fieldnames=self.FULL_FIELDS)
        self._failed_writer = csv.DictWriter(self._failed_file, fieldnames=self.FAILED_FIELDS)

        self._full_writer.writeheader()
        self._failed_writer.writeheader()

    def write_full(self, row):
        self._full_writer.writerow(row)

    def write_failed(self, row_id, consignment_number, url, error):
        self._failed_writer.writerow(
            {
                "id": row_id,
                "consignment_number": consignment_number,
                "url": url,
                "error": str(error),
            }
        )

    def close(self):
        try:
            self._full_file.close()
        finally:
            self._failed_file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
