from learn_english.crew import LearnEnglishCrew


def run():
    inputs = {
        'source': 'https://engoo.com/app/daily-news',
        'topic': 'the most interesting global news from various categories',
    }

    result = LearnEnglishCrew().crew().kickoff(inputs=inputs)
    print(result)
