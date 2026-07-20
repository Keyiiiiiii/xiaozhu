import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from api.models import VisitRecord


class ASRConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.job_id = self.scope["url_route"]["kwargs"]["job_id"]
        self.group_name = f"asr_{self.job_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        await self.check_existing_result()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def check_existing_result(self):
        try:
            visit_records = VisitRecord.objects.filter(status__in=["success", "failed"])
            for record in visit_records:
                if record.status == "success":
                    await self.send_json({
                        "status": "success",
                        "data": {
                            "segments": record.original_text,
                            "status": "done"
                        }
                    })
                    await self.close()
                    return
                elif record.status == "failed":
                    await self.send_json({
                        "status": "error",
                        "message": "转写任务已失败"
                    })
                    await self.close()
                    return
        except Exception:
            pass

    async def asr_result(self, event):
        message = event["message"]
        await self.send_json(message)
        await self.close()
