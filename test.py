from dataclasses import dataclass
from typing import List, Optional
import random


@dataclass
class Task:
    name: str
    required_skill: str
    difficulty: int


@dataclass
class Bid:
    agent_name: str
    cost: float
    estimated_time: float
    score: float


class WorkerAgent:
    def __init__(self, name: str, skills: List[str], base_cost: float, speed: float):
        self.name = name
        self.skills = skills
        self.base_cost = base_cost
        self.speed = speed

    def can_do(self, task: Task) -> bool:
        return task.required_skill in self.skills

    def bid(self, task: Task) -> Optional[Bid]:
        if not self.can_do(task):
            return None

        estimated_time = task.difficulty / self.speed
        cost = self.base_cost * task.difficulty

        # score 越低越好：综合考虑成本和时间
        score = cost + estimated_time * 10

        return Bid(
            agent_name=self.name,
            cost=round(cost, 2),
            estimated_time=round(estimated_time, 2),
            score=round(score, 2)
        )

    def execute(self, task: Task):
        print(f"    {self.name} 正在执行任务：{task.name}")
        print(f"    技能匹配：{task.required_skill}")
        print(f"    任务完成！")


class ManagerAgent:
    def __init__(self, name: str, workers: List[WorkerAgent]):
        self.name = name
        self.workers = workers

    def announce_task(self, task: Task) -> List[Bid]:
        print(f"\n{self.name} 发布任务：{task.name}")
        print(f"要求技能：{task.required_skill}, 难度：{task.difficulty}")

        bids = []

        for worker in self.workers:
            bid = worker.bid(task)
            if bid:
                bids.append(bid)
                print(
                    f"  {worker.name} 报价：成本={bid.cost}, "
                    f"时间={bid.estimated_time}, 综合分={bid.score}"
                )
            else:
                print(f"  {worker.name} 不具备技能，无法投标")

        return bids

    def select_winner(self, bids: List[Bid]) -> Optional[Bid]:
        if not bids:
            return None

        return min(bids, key=lambda bid: bid.score)

    def assign_task(self, task: Task):
        bids = self.announce_task(task)
        winner_bid = self.select_winner(bids)

        if not winner_bid:
            print("  没有 Agent 可以完成该任务")
            return

        print(f"  中标 Agent：{winner_bid.agent_name}")

        winner_agent = next(
            worker for worker in self.workers
            if worker.name == winner_bid.agent_name
        )

        winner_agent.execute(task)


def main():
    workers = [
        WorkerAgent(
            name="Agent-A",
            skills=["data_cleaning", "visualization"],
            base_cost=8,
            speed=2.0
        ),
        WorkerAgent(
            name="Agent-B",
            skills=["model_training", "data_cleaning"],
            base_cost=12,
            speed=3.5
        ),
        WorkerAgent(
            name="Agent-C",
            skills=["deployment", "model_training"],
            base_cost=10,
            speed=2.5
        ),
    ]

    manager = ManagerAgent(name="Manager-Agent", workers=workers)

    tasks = [
        Task(name="清理用户行为数据", required_skill="data_cleaning", difficulty=5),
        Task(name="训练推荐模型", required_skill="model_training", difficulty=8),
        Task(name="部署模型服务", required_skill="deployment", difficulty=6),
        Task(name="生成销售可视化图表", required_skill="visualization", difficulty=4),
    ]

    for task in tasks:
        manager.assign_task(task)


if __name__ == "__main__":
    main()