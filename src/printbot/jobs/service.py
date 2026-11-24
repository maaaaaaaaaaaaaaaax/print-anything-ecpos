from printbot.jobs.models import Job, NewJob
from printbot.jobs.ports import Clock, JobRepository
from printbot.kernel import TextSource


class JobService:
    def __init__(self, repository: JobRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    async def submit(self, chat_id: int, telegram_update_id: int, text: str) -> Job | None:
        job = NewJob(
            chat_id=chat_id,
            telegram_update_id=telegram_update_id,
            source=TextSource(text=text),
            created_at=self._clock(),
        )
        return await self._repository.add(job)
