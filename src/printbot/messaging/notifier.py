import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from printbot.jobs import Job, JobStatus

LOGGER = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def job_updated(self, job: Job) -> None:
        try:
            await self._bot.send_message(job.chat_id, _message_for(job))
        except TelegramAPIError as error:
            LOGGER.error(
                "could not notify job %s with status %s: %s",
                job.id,
                job.status,
                error,
            )


def _message_for(job: Job) -> str:
    match job.status:
        case JobStatus.RECEIVED:
            return "Queued for printing."
        case JobStatus.CONVERTING:
            return "Converting..."
        case JobStatus.READY:
            return "Ready to print."
        case JobStatus.PRINTING:
            return "Printing..."
        case JobStatus.DONE:
            return "Printed."
        case JobStatus.FAILED:
            return f"Print failed: {job.error or 'unknown error'}"
