from dataclasses import dataclass
from pathlib import Path
import tempfile

@dataclass(frozen=True)
class ProcessingResult:
    job_id: str
    document_id: str
    memory_id: str
class ProcessingWorker:
    def __init__(self, *, storage, repository, pipelines): self.storage=storage; self.repository=repository; self.pipelines=pipelines
    async def run(self, job_id: str, user_id: str) -> ProcessingResult:
        job=self.repository.get_job(job_id,user_id); document=self.repository.get_document(job["document_id"],user_id)
        values={"status":"processing","progress":0}
        self.repository.update_job(job_id,user_id,values)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/document["file_name"]; path.write_bytes(self.storage.download(f"{user_id}/{document['id']}/{document['file_name']}"))
            async def stage(name,progress): self.repository.update_job(job_id,user_id,{"current_stage":str(getattr(name,"value",name)),"progress":progress})
            result=await self.pipelines.build(user_id).run(str(path),user_id=user_id,document_id=document["id"],document_version=str(document.get("version",1)),stage_callback=stage)
        discovered={"memories":1,"entities":len(result.knowledge.entities),"relationships":len(result.relationships.relationships),"timelineEvents":len(result.temporal.events),"highlights":[]}
        self.repository.update_job(job_id,user_id,{"status":"complete","progress":100,"discovered":discovered})
        return ProcessingResult(job_id,document["id"],result.memory_id)
