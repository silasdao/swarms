from swarms import DialogueSimulator, Worker


def select_next_speaker(step: int, agents) -> int:
    return (step) % len(agents)


debate = DialogueSimulator(Worker, select_next_speaker)

debate.run()
