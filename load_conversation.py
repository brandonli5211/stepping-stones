import json
from urllib.request import urlopen

from pymongo import MongoClient


ABCD_SAMPLE_URL = "https://raw.githubusercontent.com/asappresearch/abcd/master/data/abcd_sample.json"


def load_conversations():
    with urlopen(ABCD_SAMPLE_URL, timeout=30) as response:
        samples = json.load(response)

    if not isinstance(samples, list) or not samples:
        raise ValueError("The ABCD sample file did not contain a conversation list.")

    conversations = []
    for api_id, sample in enumerate(samples, start=1):
        original = sample.get("original")
        if not isinstance(original, list):
            raise ValueError(f"ABCD conversation {sample.get('convo_id')} has no original transcript.")

        transcript = []
        for turn in original:
            if not isinstance(turn, list) or len(turn) != 2:
                raise ValueError(f"ABCD conversation {sample.get('convo_id')} has an invalid transcript turn.")
            speaker, text = turn
            transcript.append({"speaker": speaker.title(), "text": text})

        conversations.append({
            "_id": str(api_id),
            "conversation_id": str(sample["convo_id"]),
            "transcript": transcript,
        })

    return conversations


def main():
    conversations = load_conversations()
    with MongoClient("mongodb://localhost:27017/") as client:
        collection = client["genesys_poc"]["conversations"]
        for conversation in conversations:
            collection.replace_one({"_id": conversation["_id"]}, conversation, upsert=True)

    print(f"Loaded {len(conversations)} ABCD sample conversations into genesys_poc.conversations.")
    for conversation in conversations:
        print(f"API ID {conversation['_id']} -> ABCD conversation {conversation['conversation_id']}")


if __name__ == "__main__":
    main()