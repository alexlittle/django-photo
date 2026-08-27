"""Tests for the ``report_full`` management command.

A runner: it calls fifteen other commands in sequence. ``call_command`` is
patched at this module, so these tests cover the orchestration -- which
commands, in what order, with what arguments -- rather than re-running the
individual commands, which have their own test files.

report_missing_country is deliberately excluded: it blocks on input(), which
would hang this command when run unattended (e.g. from cron). Run it
separately when wanted.
"""

from unittest.mock import patch

from tests.base import CommandTestCase

COMMAND = "report_full"
TARGET = "photo.management.commands.report_full.call_command"

EXPECTED_SEQUENCE = [
    "files_deep_structure",
    "files_scan_albums",
    "files_scan_photos",
    "files_scan_photos",
    "files_duplicate_filenames",
    "integrity_uncategorised_tags",
    "integrity_remove_unused_tags",
    "integrity_album_covers",
    "integrity_albums_no_title",
    "integrity_only_one_tag",
    "integrity_small_albums",
    "integrity_remove_empty_albums",
    "report_missing_coordinates",
    "report_missing_source",
    "tag_diff",
]


class ReportFullTests(CommandTestCase):
    def invoke(self):
        with patch(TARGET) as call_command:
            self.run_command(COMMAND)
        return call_command

    def called_names(self, call_command):
        return [call.args[0] for call in call_command.call_args_list]

    def test_every_command_runs_in_order(self):
        call_command = self.invoke()

        self.assertEqual(self.called_names(call_command), EXPECTED_SEQUENCE)

    def test_fifteen_commands_are_run(self):
        call_command = self.invoke()

        self.assertEqual(call_command.call_count, 15)

    def test_deep_structure_gets_a_threshold(self):
        call_command = self.invoke()

        call_command.assert_any_call("files_deep_structure", count=2)

    def test_small_albums_gets_a_threshold(self):
        call_command = self.invoke()

        call_command.assert_any_call("integrity_small_albums", count=10)

    def test_photo_scanning_runs_both_passes(self):
        call_command = self.invoke()

        call_command.assert_any_call("files_scan_photos", files=True)
        call_command.assert_any_call("files_scan_photos", db=True)

    def test_no_destructive_flags_are_passed_to_the_scanners(self):
        # files_scan_photos --autodelete is not used here, so the scan reports
        # rather than deletes.
        call_command = self.invoke()

        for call in call_command.call_args_list:
            self.assertNotIn("autodelete", call.kwargs)

    def test_the_run_includes_two_commands_that_delete_data(self):
        # Worth being explicit about: despite the name, report_full is not
        # read-only. integrity_remove_unused_tags and
        # integrity_remove_empty_albums both delete rows outright, and neither
        # asks for confirmation. Anyone running this expecting a report gets
        # mutations too.
        call_command = self.invoke()
        names = self.called_names(call_command)

        self.assertIn("integrity_remove_unused_tags", names)
        self.assertIn("integrity_remove_empty_albums", names)

    def test_tag_removal_happens_after_the_tag_report(self):
        # Ordering fix: unused tags are now deleted after
        # integrity_uncategorised_tags runs, so a tag removed in this pass
        # still showed up in that report first.
        names = self.called_names(self.invoke())

        self.assertGreater(
            names.index("integrity_remove_unused_tags"),
            names.index("integrity_uncategorised_tags"),
        )

    def test_album_removal_happens_after_the_album_reports(self):
        names = self.called_names(self.invoke())

        self.assertGreater(
            names.index("integrity_remove_empty_albums"),
            names.index("integrity_albums_no_title"),
        )

    def test_the_run_does_not_include_the_interactive_command(self):
        # report_missing_country blocks on input(), which would hang
        # report_full when run unattended (e.g. from cron), so it is
        # deliberately excluded here -- run it separately when wanted.
        names = self.called_names(self.invoke())

        self.assertNotIn("report_missing_country", names)

    def test_a_failure_partway_stops_the_run(self):
        # No per-command error handling, so one broken command abandons every
        # report after it.
        with (
            patch(TARGET, side_effect=[None, RuntimeError("boom")]) as call_command,
            self.assertRaises(RuntimeError),
        ):
            self.run_command(COMMAND)

        self.assertEqual(call_command.call_count, 2)
