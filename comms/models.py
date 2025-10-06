from django.db import models

class Message(models.Model):
    team = models.ForeignKey("game.Team", on_delete=models.CASCADE, related_name="messages")
    player = models.ForeignKey("game.Player", on_delete=models.SET_NULL, null=True, blank=True)
    text = models.CharField(max_length=300)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["team", "id"])]
