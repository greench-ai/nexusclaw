"""
NexusClaw EvoClaw Heartbeat
Runs every 5 minutes. Ingest → Reflect → Brain → Propose → Govern → Apply → Log → State → Notify
"""
import os, json, time, asyncio
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path(os.environ.get("NEXUS_WORKSPACE", "~/.nexusclaw")).expanduser()
MEMORY_DIR = WORKSPACE / "memory"
EXPERIENCES_DIR = MEMORY_DIR / "experiences"
REFLECTIONS_DIR = MEMORY_DIR / "reflections"
STATE_FILE = MEMORY_DIR / "evoclaw-state.json"
SOUL_FILE = WORKSPACE / "soul.json"
CONFIG_FILE = WORKSPACE / "evoclaw-config.json"

class EvoClawHeartbeat:
    def __init__(self):
        self.heartbeat_count = 0
        self.last_reflection = None
        self.last_brain_run = None
        self.load_state()
    
    def load_state(self):
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                d = json.load(f)
                self.heartbeat_count = d.get("heartbeat_count", 0)
                self.last_reflection = d.get("last_reflection")
                self.last_brain_run = d.get("last_brain_run")
    
    def save_state(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump({
                "heartbeat_count": self.heartbeat_count,
                "last_reflection": self.last_reflection,
                "last_brain_run": self.last_brain_run,
                "last_heartbeat": datetime.utcnow().isoformat() + "Z"
            }, f, indent=2)
    
    def run(self):
        """Execute one heartbeat cycle."""
        self.heartbeat_count += 1
        hb = self.heartbeat_count
        ts = datetime.utcnow().isoformat() + "Z"
        
        # Step 1: Ingest — check for unlogged experiences
        self.ingest(hb, ts)
        
        # Step 2: Reflect — process notable/pivotal experiences
        self.reflect(hb, ts)
        
        # Step 3: Brain — run three brain organs
        self.run_brain_organs(hb, ts)
        
        # Step 4-6: Propose → Govern → Apply (SOUL updates)
        self.evolve_soul(hb, ts)
        
        # Step 7-9: Log → State → Notify
        self.save_state()
        self.notify(hb, ts)
        
        return {"heartbeat": hb, "status": "ok", "timestamp": ts}
    
    def ingest(self, hb: int, ts: str):
        """Check for new experiences to log."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        exp_file = EXPERIENCES_DIR / f"{today}.jsonl"
        if not exp_file.exists():
            return {"logged": 0}
        
        with open(exp_file) as f:
            lines = f.readlines()
        
        new_count = 0
        for line in lines:
            try:
                exp = json.loads(line)
                if not exp.get("logged"):
                    exp["logged"] = True
                    new_count += 1
            except: pass
        
        return {"ingested": new_count}
    
    def reflect(self, hb: int, ts: str):
        """Reflect on pivotal/notable experiences."""
        min_interval = 30  # minutes between reflections
        if self.last_reflection:
            last = datetime.fromisoformat(self.last_reflection.replace("Z", "+00:00"))
            if datetime.now(last.tzinfo) - last < timedelta(minutes=min_interval):
                return {"reflected": False, "reason": "too_soon"}
        
        today = datetime.utcnow().strftime("%Y-%m-%d")
        exp_file = EXPERIENCES_DIR / f"{today}.jsonl"
        if not exp_file.exists():
            return {"reflected": False}
        
        with open(exp_file) as f:
            lines = [json.loads(l) for l in f.readlines() if l.strip()]
        
        # Find unreflected pivotal experiences
        pivotal = [l for l in lines if l.get("significance") == "pivotal" and not l.get("reflected")]
        
        if pivotal:
            REFLECTIONS_DIR.mkdir(parents=True, exist_ok=True)
            existing = list(REFLECTIONS_DIR.glob("REF-*.json"))
            next_num = len(existing) + 1
            ref_id = f"REF-{datetime.utcnow().strftime('%Y%m%d')}-{next_num:03d}"
            
            reflection = {
                "id": ref_id,
                "timestamp": ts,
                "source_ids": [p["id"] for p in pivotal],
                "type": "pivotal",
                "content": "; ".join([p.get("content","")[:200] for p in pivotal]),
                "insights": [f"Pivotal: {p.get('content','')[:150]}" for p in pivotal[:3]],
                "tags": list(set(sum([p.get("tags",[]) for p in pivotal], [])))
            }
            
            with open(REFLECTIONS_DIR / f"{ref_id}.json", "w") as f:
                json.dump(reflection, f, indent=2)
            
            self.last_reflection = ts
            
            # Mark experiences as reflected
            for line in lines:
                if line.get("id") in [p["id"] for p in pivotal]:
                    line["reflected"] = True
            with open(exp_file, "w") as f:
                for l in lines:
                    f.write(json.dumps(l) + "\n")
            
            return {"reflected": True, "reflection_id": ref_id}
        
        return {"reflected": False, "reason": "no_pivotal"}
    
    def run_brain_organs(self, hb: int, ts: str):
        """Run consolidation, anchor audit, curiosity tracker."""
        results = {}
        
        # 1. Consolidation Layer
        try:
            from ..brain.consolidate import ConsolidationLayer
            cl = ConsolidationLayer()
            r = cl.run()
            results["consolidation"] = r
        except Exception as e:
            results["consolidation"] = {"error": str(e)}
        
        # 2. Anchor Audit
        try:
            from ..brain.anchor_audit import AnchorAudit
            aa = AnchorAudit()
            r = aa.check()
            results["anchor_audit"] = r
        except Exception as e:
            results["anchor_audit"] = {"error": str(e)}
        
        # 3. Curiosity Tracker
        try:
            from ..brain.curiosity import CuriosityTracker
            ct = CuriosityTracker()
            r = ct.heartbeat_summary()
            results["curiosity"] = r
        except Exception as e:
            results["curiosity"] = {"error": str(e)}
        
        self.last_brain_run = ts
        return results
    
    def evolve_soul(self, hb: int, ts: str):
        """Check for SOUL proposals and apply if warranted."""
        # TODO: implement full proposal/governance cycle
        return {"evolved": False, "reason": "not_implemented"}
    
    def notify(self, hb: int, ts: str):
        """Log heartbeat to pipeline record."""
        pipeline_file = MEMORY_DIR / "pipeline" / f"{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        pipeline_file.parent.mkdir(exist_ok=True)
        
        record = {"heartbeat": hb, "timestamp": ts, "status": "ok"}
        with open(pipeline_file, "a") as f:
            f.write(json.dumps(record) + "\n")
        
        return record

def run_heartbeat():
    """CLI entry point."""
    hb = EvoClawHeartbeat()
    result = hb.run()
    print(f"Heartbeat #{result['heartbeat']} — {result['status']}")

if __name__ == "__main__":
    run_heartbeat()
