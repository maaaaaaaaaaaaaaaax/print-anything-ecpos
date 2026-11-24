import pytest

from printbot.jobs import InvalidJobTransitionError, JobStatus, transition_job_status


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (JobStatus.RECEIVED, JobStatus.CONVERTING),
        (JobStatus.CONVERTING, JobStatus.READY),
        (JobStatus.CONVERTING, JobStatus.FAILED),
        (JobStatus.READY, JobStatus.PRINTING),
        (JobStatus.PRINTING, JobStatus.DONE),
        (JobStatus.PRINTING, JobStatus.FAILED),
    ],
)
def test_allowed_job_transitions(source: JobStatus, target: JobStatus) -> None:
    assert transition_job_status(source, target) is target


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (JobStatus.RECEIVED, JobStatus.READY),
        (JobStatus.READY, JobStatus.DONE),
        (JobStatus.DONE, JobStatus.PRINTING),
        (JobStatus.FAILED, JobStatus.READY),
    ],
)
def test_invalid_job_transitions_are_rejected(source: JobStatus, target: JobStatus) -> None:
    with pytest.raises(InvalidJobTransitionError):
        transition_job_status(source, target)
