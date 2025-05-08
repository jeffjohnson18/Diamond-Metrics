from django.db import models
from django.contrib.auth.models import User

class Pitcher(models.Model):
    player_name = models.CharField(max_length=100)
    player_image = models.URLField()
    team_name = models.CharField(max_length=100)
    team_logo = models.URLField()
    stand_side = models.CharField(max_length=1)
    pitch_type = models.CharField(max_length=2)
    velocity_range = models.CharField(max_length=20)
    usage_rate = models.CharField(max_length=10)
    zone_rate = models.CharField(max_length=10)
    avg_spin_rate = models.FloatField()
    avg_horz_break = models.FloatField()
    avg_induced_vert_break = models.FloatField()
    arm_angle = models.FloatField()
    throws = models.CharField(max_length=1)
    heatmap_path = models.CharField(max_length=200)

    def __str__(self):
        return self.player_name

class FavoritePitcher(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    pitcher = models.ForeignKey(Pitcher, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'pitcher')

    def __str__(self):
        return f"{self.user.username}'s favorite: {self.pitcher.player_name}"
