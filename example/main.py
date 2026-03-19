from sinch_messaging import SinchClient


def main() -> None:
    # This example demonstrates the SDK interface.
    # The exercise API is simplified/fictional, so this script is illustrative
    # unless used against a compatible test server.
    with SinchClient(auth_token="your-token") as client:
        message = client.messages.send_sms(
            to="+34600111222",
            text="Hello from the example project",
        )
        print("Sent:", message)

        latest = client.messages.get(message.message_id)
        print("Current status:", latest.status)

        for item in client.messages.iterate(page_size=50):
            print(item.message_id, item.status)


if __name__ == "__main__":
    main()