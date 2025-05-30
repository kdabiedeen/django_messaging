from celery import shared_task
import requests


@shared_task(bind=True, max_retries=5)
def send_message_to_provider(self, message_payload, provider_url):
    try:
        response = requests.post(provider_url, json=message_payload)

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after is not None:
                # Retry-After might be in seconds or as an HTTP-date
                try:
                    countdown = int(retry_after)
                except ValueError:
                    # Handle HTTP-date format if needed in future
                    countdown = 60  # fallback
            else:
                countdown = 2 ** self.request.retries  # exponential backoff fallback

            raise self.retry(
                exc=Exception("Rate limited (429)"),
                countdown=countdown
            )

        elif response.status_code != 200:
            raise Exception(f"Provider failed with status {response.status_code}: {response.text}")

        return {"status": "success", "response": response.json()}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
