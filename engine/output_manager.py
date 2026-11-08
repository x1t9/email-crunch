"""
Output Management & File Post-Processing Module for Email Crunch.
Handles CSV exports, automatic row chunk splitting, deduplication,
and file operations (move, rename, delete, keep).
"""

import os
import csv
import shutil
from datetime import datetime
from typing import List, Set, Dict, Optional, Tuple


class OutputManager:
    """
    Manages CSV export destinations, auto-splitting large email lists,
    and post-processing source files upon successful completion.
    """

    def __init__(
        self,
        destination_mode: str = "same_folder",  # "same_folder", "custom_folder", "merge_all"
        custom_folder: str = "",
        file_prefix: str = "contact_list_",
        auto_split: bool = True,
        split_limit: int = 20000,
        global_dedupe: bool = True,
        post_action: str = "keep",  # "keep", "move", "delete", "rename"
        archive_folder: str = "",
        rename_prefix: str = "Scraped_",
        rename_suffix: str = ""
    ):
        self.destination_mode = destination_mode
        self.custom_folder = custom_folder
        self.file_prefix = file_prefix if file_prefix else "contact_list_"
        self.auto_split = auto_split
        self.split_limit = max(1, split_limit)
        self.global_dedupe = global_dedupe
        self.post_action = post_action
        self.archive_folder = archive_folder
        self.rename_prefix = rename_prefix
        self.rename_suffix = rename_suffix
        
        # State tracking for merged mode
        self.merged_records: List[Tuple[str, str]] = []  # (email, source_file)
        self.global_seen_emails: Set[str] = set()

    def add_results_for_file(self, source_path: str, emails: List[str]) -> Optional[str]:
        """
        Processes extracted emails for a specific source file.
        In 'same_folder' or 'custom_folder' mode, writes the file's individual CSV.
        In 'merge_all' mode, collects emails to be finalized at the end.
        Returns the output file path or a summary string.
        """
        if not emails:
            return None

        clean_emails = []
        for e in emails:
            e_lower = e.strip().lower()
            if self.global_dedupe:
                if e_lower not in self.global_seen_emails:
                    self.global_seen_emails.add(e_lower)
                    clean_emails.append(e_lower)
            else:
                clean_emails.append(e_lower)

        if not clean_emails:
            return None

        # If merged mode, accumulate for batch export
        if self.destination_mode == "merge_all":
            for em in clean_emails:
                self.merged_records.append((em, os.path.basename(source_path)))
            return "Queued for consolidated master CSV"

        # Determine output directory
        if self.destination_mode == "custom_folder" and self.custom_folder:
            out_dir = self.custom_folder
            os.makedirs(out_dir, exist_ok=True)
        else:
            out_dir = os.path.dirname(os.path.abspath(source_path))

        base_name = os.path.splitext(os.path.basename(source_path))[0]
        
        # Check if splitting is necessary
        if self.auto_split and len(clean_emails) > self.split_limit:
            created_files = []
            chunk_idx = 1
            for i in range(0, len(clean_emails), self.split_limit):
                chunk = clean_emails[i:i + self.split_limit]
                chunk_filename = f"{self.file_prefix}{base_name}_{chunk_idx}.csv"
                chunk_path = os.path.join(out_dir, chunk_filename)
                self._write_csv(chunk_path, [(em, os.path.basename(source_path)) for em in chunk])
                created_files.append(chunk_path)
                chunk_idx += 1
            return f"Saved {len(created_files)} chunked CSVs"
        else:
            out_filename = f"{self.file_prefix}{base_name}.csv"
            out_path = os.path.join(out_dir, out_filename)
            self._write_csv(out_path, [(em, os.path.basename(source_path)) for em in clean_emails])
            return out_path

    def finalize_merged_export(self) -> List[str]:
        """
        Exports all accumulated merged records into consolidated CSV(s).
        Respects split_limit if auto_split is enabled.
        Returns list of created master CSV file paths.
        """
        if self.destination_mode != "merge_all" or not self.merged_records:
            return []

        if self.custom_folder:
            out_dir = self.custom_folder
            os.makedirs(out_dir, exist_ok=True)
        else:
            out_dir = os.path.abspath(os.getcwd())

        created_files = []
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.auto_split and len(self.merged_records) > self.split_limit:
            chunk_idx = 1
            for i in range(0, len(self.merged_records), self.split_limit):
                chunk = self.merged_records[i:i + self.split_limit]
                filename = f"{self.file_prefix}master_{now_str}_part{chunk_idx}.csv"
                out_path = os.path.join(out_dir, filename)
                self._write_csv(out_path, chunk)
                created_files.append(out_path)
                chunk_idx += 1
        else:
            filename = f"{self.file_prefix}master_{now_str}.csv"
            out_path = os.path.join(out_dir, filename)
            self._write_csv(out_path, self.merged_records)
            created_files.append(out_path)

        return created_files

    def _write_csv(self, file_path: str, records: List[Tuple[str, str]]):
        """Writes records [(email, source_file)] into a clean CSV file."""
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Email", "Source_File", "Date_Extracted"])
            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for email, source in records:
                writer.writerow([email, source, now_iso])

    def apply_post_processing(self, file_path: str) -> Tuple[bool, str]:
        """
        Executes post-processing rules on a source file after extraction:
        1. Keep original (do nothing)
        2. Move to folder
        3. Delete original file
        4. Rename original file
        Returns: (success_bool, message)
        """
        if not os.path.exists(file_path):
            return False, "File does not exist"

        if self.post_action == "keep":
            return True, "Original kept"

        elif self.post_action == "delete":
            try:
                os.remove(file_path)
                return True, "Original deleted"
            except Exception as e:
                return False, f"Failed to delete: {e}"

        elif self.post_action == "move":
            if not self.archive_folder:
                return False, "Archive folder not set"
            try:
                os.makedirs(self.archive_folder, exist_ok=True)
                dest = os.path.join(self.archive_folder, os.path.basename(file_path))
                # If destination already exists, generate unique name
                if os.path.exists(dest):
                    stem, ext = os.path.splitext(os.path.basename(file_path))
                    ts = datetime.now().strftime("%Y%m%d%H%M%S")
                    dest = os.path.join(self.archive_folder, f"{stem}_{ts}{ext}")
                shutil.move(file_path, dest)
                return True, f"Moved to {os.path.basename(dest)}"
            except Exception as e:
                return False, f"Failed to move: {e}"

        elif self.post_action == "rename":
            try:
                parent = os.path.dirname(os.path.abspath(file_path))
                orig_name = os.path.basename(file_path)
                stem, ext = os.path.splitext(orig_name)
                new_name = f"{self.rename_prefix}{stem}{self.rename_suffix}{ext}"
                new_path = os.path.join(parent, new_name)
                os.rename(file_path, new_path)
                return True, f"Renamed to {new_name}"
            except Exception as e:
                return False, f"Failed to rename: {e}"

        return True, "No action"
