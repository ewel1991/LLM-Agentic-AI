from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeWebsiteTool


@CrewBase
class LearnEnglishCrew():
    """Załoga projektu LearnEnglish"""

    # Ścieżki do plików konfiguracyjnych
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def content_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['content_analyst'],
            tools=[ScrapeWebsiteTool()],
            verbose=True
        )

    @agent
    def newsletter_editor(self) -> Agent:
        return Agent(
            config=self.agents_config['newsletter_editor'],
            verbose=True
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'],
        )

    @task
    def newsletter_task(self) -> Task:
        return Task(
            config=self.tasks_config['newsletter_task'],
            context=[self.analysis_task()]  # Tutaj łączymy zadania!
        )

    @crew
    def crew(self) -> Crew:
        """Tworzy załogę LearnEnglish"""
        return Crew(
            agents=self.agents,  # Automatycznie zbiera metody z dekoratorem @agent
            tasks=self.tasks,   # Automatycznie zbiera metody z dekoratorem @task
            process=Process.sequential,
            verbose=True,
        )
