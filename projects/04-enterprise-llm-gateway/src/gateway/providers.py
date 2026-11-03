import asyncio


class ProviderError(Exception):
    def __init__(self, kind, safe=True):
        self.kind, self.safe = kind, safe


class Breaker:
    def __init__(self, clock, transition):
        self.clock, self.transition = clock, transition
        self.state = "closed"
        self.failures = 0
        self.until = 0
        self.probing = False
        self.epoch = 0

    def available(self):
        return self.state != "open" or self.clock() >= self.until

    def enter(self):
        if not self.available() or self.probing:
            raise ProviderError("circuit_open")
        if self.state == "open":
            self.change("half_open")
            self.probing = True
        return self.epoch

    def change(self, state):
        self.state = state
        self.epoch += 1
        self.transition(state)

    def result(self, success, permit=None):
        if permit is not None and permit != self.epoch:
            return
        self.probing = False
        if success:
            self.failures = 0
            if self.state != "closed":
                self.change("closed")
        else:
            self.failures += 1
            if self.failures >= 2 or self.state == "half_open":
                self.until = self.clock() + 0.1
                self.change("open")


class SimulatedProvider:
    replay_safe = (
        True  # Pure deterministic computation, no external side effects or bill.
    )

    def __init__(self):
        self.calls = {}

    async def generate(self, model, profile, prompt, output):
        self.calls[model] = self.calls.get(model, 0) + 1
        mode = profile["behavior"]
        if mode in ("timeout", "slow"):
            await asyncio.sleep(0.2)
        else:
            await asyncio.sleep(profile["latency"])
        if mode in ("429", "500", "unavailable"):
            raise ProviderError(mode)
        if mode == "intermittent" and self.calls[model] % 2:
            raise ProviderError("500")
        usage = {"input": len(prompt.encode()), "output": min(output, 8)}
        if mode == "missing_usage":
            usage = None
        if mode == "incorrect_usage":
            usage = {"input": -1, "output": 999999}
        return {"text": f"synthetic {model} answer", "usage": usage}
