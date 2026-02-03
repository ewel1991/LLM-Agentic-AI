from learn_english.crew import LearnEnglishCrew


def run():
    inputs = {
        'source': 'https://www.bbc.com/news/science-environment-56837908',
        'topic': 'climate change and technology',
    }

    result = LearnEnglishCrew().crew().kickoff(inputs=inputs)
    print(result)


if __name__ == "__main__":
    run()
