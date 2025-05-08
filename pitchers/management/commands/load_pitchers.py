import json
from django.core.management.base import BaseCommand
from pitchers.models import Pitcher

class Command(BaseCommand):
    help = 'Load pitcher data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file containing pitcher data')

    def handle(self, *args, **options):
        json_file = options['json_file']
        
        with open(json_file, 'r') as f:
            pitchers_data = json.load(f)
        
        for pitcher_data in pitchers_data:
            Pitcher.objects.get_or_create(
                player_name=pitcher_data['player_name'],
                defaults={
                    'player_image': pitcher_data['player_image'],
                    'team_name': pitcher_data['team_name'],
                    'team_logo': pitcher_data['team_logo'],
                    'stand_side': pitcher_data['stand_side'],
                    'pitch_type': pitcher_data['pitch_type'],
                    'velocity_range': pitcher_data['velocity_range'],
                    'usage_rate': pitcher_data['usage_rate'],
                    'zone_rate': pitcher_data['zone_rate'],
                    'avg_spin_rate': pitcher_data['avg_spin_rate'],
                    'avg_horz_break': pitcher_data['avg_horz_break'],
                    'avg_induced_vert_break': pitcher_data['avg_induced_vert_break'],
                    'arm_angle': pitcher_data['arm_angle'],
                    'throws': pitcher_data['throws'],
                    'heatmap_path': pitcher_data['heatmap_path'],
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded pitcher data')) 