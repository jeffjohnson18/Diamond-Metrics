from django.contrib import admin
from .models import Pitcher, FavoritePitcher

@admin.register(Pitcher)
class PitcherAdmin(admin.ModelAdmin):
    list_display = ('player_name', 'team_name', 'pitch_type', 'throws')
    search_fields = ('player_name', 'team_name')
    list_filter = ('team_name', 'pitch_type', 'throws')

@admin.register(FavoritePitcher)
class FavoritePitcherAdmin(admin.ModelAdmin):
    list_display = ('user', 'pitcher', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'pitcher__player_name')
