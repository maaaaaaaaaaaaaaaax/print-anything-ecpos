from enum import StrEnum


class JobStatus(StrEnum):
    RECEIVED = "received"
    CONVERTING = "converting"
    READY = "ready"
    PRINTING = "printing"
    DONE = "done"
    FAILED = "failed"


ALLOWED_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.RECEIVED: frozenset({JobStatus.CONVERTING}),
    JobStatus.CONVERTING: frozenset({JobStatus.READY, JobStatus.FAILED}),
    JobStatus.READY: frozenset({JobStatus.PRINTING}),
    JobStatus.PRINTING: frozenset({JobStatus.DONE, JobStatus.FAILED}),
    JobStatus.DONE: frozenset(),
    JobStatus.FAILED: frozenset(),
}


class InvalidJobTransitionError(ValueError):
    pass


def transition_job_status(source: JobStatus, target: JobStatus) -> JobStatus:
    if target not in ALLOWED_TRANSITIONS[source]:
        raise InvalidJobTransitionError(f"cannot transition job from {source} to {target}")
    return target
