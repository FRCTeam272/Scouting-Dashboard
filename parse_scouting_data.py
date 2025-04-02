# if you decided to read this file to see if I exposed a TBA API key, lets just be cool ok
# I need this to run on a bunch of people's laptops and I can't walk everyone through setting up the keys for every person
# so I'm just going to use my key here and regenerate it if TBA emails me and complains
TBA_API_KEY = "07tRTM0dcdQIzRCO5AnyGnKQRrzeJxwOMlsKx8HTpBlNABoQYSsI4U9HjregeNWL"
# District key for your region (e.g., '2024ne' for New England)
DISTRICT_KEY = "2025fma"  # Replace with your district key
CURRENT_EVENT_CODE = "2025paben" # "2025mrcmp"
CURRENT_EVENT_NAME = "2025 PABEN"  # Display name for the event


try :
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    from pathlib import Path
    import webbrowser
    import os
    import bs4
    import requests
    from typing import List, Dict
    import json
except ImportError:
    import subprocess
    for package in ["pandas", "numpy", "plotly", "bs4", "requests"]:
        try:
            subprocess.check_call(['pip', 'install', package])
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}")
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    from pathlib import Path
    import webbrowser
    import os
    import bs4
    import requests
    from typing import List, Dict
    import json

def get_tba_team_names(team_numbers: List[int], api_key: str) -> Dict[int, str]:
    """Fetch team names from The Blue Alliance API"""
    team_names = {}
    headers = {'X-TBA-Auth-Key': api_key}
    base_url = 'https://www.thebluealliance.com/api/v3'
    
    for team_number in team_numbers:
        try:
            response = requests.get(
                f'{base_url}/team/frc{team_number}',
                headers=headers
            )
            if response.status_code == 200:
                team_data = response.json()
                team_names[team_number] = team_data.get('nickname', f'Team {team_number}')
            else:
                team_names[team_number] = f'Team {team_number}'
        except Exception as e:
            print(f"Error fetching data for team {team_number}: {e}")
            team_names[team_number] = f'Team {team_number}'
    
    return team_names

def get_team_events(team_number: int, year: int, api_key:str = TBA_API_KEY) -> list:
    """
    Fetch events attended by a team in a specific year from The Blue Alliance API
    
    Args:
        team_number (int): The FRC team number
        year (int): The year to check events for
        api_key (str): The Blue Alliance API key
    
    Returns:
        list: List of events with their details
    """
    headers = {'X-TBA-Auth-Key': api_key}
    base_url = 'https://www.thebluealliance.com/api/v3'
    
    try:
        response = requests.get(
            f'{base_url}/team/frc{team_number}/events/{year}',
            headers=headers
        )
        if response.status_code == 200:
            events = response.json()
            return [{
                'name': event['name'],
                'start_date': event['start_date'],
                'end_date': event['end_date'],
                'location': event['city'] + ', ' + event['state_prov'],
                'event_code': event['event_code']
            } for event in events]
        else:
            print(f"Error: Status code {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching events: {e}")
        return []

def get_district_rankings(district_key: str, api_key: str) -> Dict[int, dict]:
    """Fetch district rankings from The Blue Alliance API"""
    rankings = {}
    headers = {'X-TBA-Auth-Key': api_key}
    base_url = 'https://www.thebluealliance.com/api/v3'
    
    try:
        response = requests.get(
            f'{base_url}/district/{district_key}/rankings',
            headers=headers
        )
        if response.status_code == 200:
            rankings_data = response.json()
            for rank in rankings_data:
                team_number = int(rank['team_key'].replace('frc', ''))
                rankings[team_number] = {
                    'rank': rank['rank'],
                    'total_points': rank['point_total'],
                }
        else:
            print(f"Error fetching district rankings: {response.status_code}")
    except Exception as e:
        print(f"Error fetching district rankings: {e}")
    
    return rankings

def get_team_schedule(team_number: int, event_code: str, api_key: str) -> list:
    """Fetch a team's schedule for a specific event from The Blue Alliance API"""
    headers = {'X-TBA-Auth-Key': api_key}
    base_url = 'https://www.thebluealliance.com/api/v3'
    
    try:
        response = requests.get(
            f'{base_url}/team/frc{team_number}/event/{event_code}/matches',
            headers=headers
        )
        if response.status_code == 200:
            matches = response.json()
            # Sort matches by type (QM, SF, F) and then by match number
            def match_sort_key(match):
                match_type = match['comp_level']
                match_num = match['match_number']
                # Assign priority to match types (1 for QM, 2 for SF, 3 for F)
                type_priority = {'qm': 1, 'sf': 2, 'f': 3}.get(match_type, 4)
                return (type_priority, match_num)
            return sorted(matches, key=match_sort_key)
        else:
            print(f"Error fetching schedule: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching schedule: {e}")
        return []

def get_event_rankings(event_code: str, api_key: str) -> Dict[int, dict]:
    """Fetch event rankings from The Blue Alliance API"""
    rankings = {}
    headers = {'X-TBA-Auth-Key': api_key}
    base_url = 'https://www.thebluealliance.com/api/v3'
    
    try:
        response = requests.get(
            f'{base_url}/event/{event_code}/teams/statuses',
            headers=headers
        )
        if response.status_code == 200:
            rankings_data = response.json()
            # The API returns a list of rankings, where each item is a dict with team data
            for rank in rankings_data:
                # Extract team number from team_key (format: 'frc1234')
                team_number = int(rank.replace('frc', ''))
                team_data = rankings_data[rank]
                if 'qual' in team_data and team_data['qual'] and 'ranking' in team_data['qual']:
                    ranking = team_data['qual']['ranking']
                    rankings[team_number] = {
                        'rank': ranking.get('rank', 0),
                        'record': ranking.get('record', {
                            'wins': 0,
                            'losses': 0, 
                            'ties': 0
                        }),
                        'dq': ranking.get('dq', 0),
                        'matches_played': ranking.get('matches_played', 0)
                    }
        else:
            print(f"Error fetching event rankings: {response.status_code}")
            print(f"Response content: {response.text}")
    except Exception as e:
        print(f"Error fetching event rankings: {e}")
        if 'response' in locals():
            print(f"Response content: {response.text}")
    return rankings

def save_graph(fig, filename):
    """Save a plotly figure to an HTML file."""
    # Create graphs directory if it doesn't exist
    graphs_dir = Path('team_pages/graphs')
    graphs_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the plot using forward slashes
    output_path = f"{graphs_dir}//{filename}"
    fig.write_html(str(output_path))

def create_team_page(team_data, team_number, team_name, rankings):
    """Create an HTML page for a specific team with their statistics and visualizations."""
    
    # Get current timestamp
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Get team ranking
    team_rank = rankings.get(team_number, {})
    rank_text = f"Rank: {team_rank.get('rank', 'N/A')}"
    if team_rank.get('record'):
        rank_text += f" ({team_rank['record']['wins']}-{team_rank['record']['losses']}-{team_rank['record']['ties']})"
    
    # Calculate key statistics
    total_matches = len(team_data)
    avg_coral_l1 = team_data['teleopCoralPlaceL1Count'].mean()
    avg_coral_l2 = team_data['teleopCoralPlaceL2Count'].mean()
    avg_coral_l3 = team_data['teleopCoralPlaceL3Count'].mean()
    avg_coral_l4 = team_data['teleopCoralPlaceL4Count'].mean()
    avg_algae_net = team_data['teleopAlgaePlaceNetShot'].mean()
    avg_algae_processor = team_data['teleopAlgaePlaceProcessor'].mean()
    # Calculate endgame points - only count the highest scoring action per match
    endgame_points = team_data.apply(lambda row: 
        max([
            12 if row['deepClimbAttempted'] and not row['climbFailed'] else 0,  # Deep climb is worth 12 points
            6 if row['shallowClimbAttempted'] and not row['climbFailed'] else 0,  # Shallow climb is worth 6 points
            2 if row['parkAttempted'] else 0  # Park is worth 2 points
        ]), 
        axis=1
    ).mean()
    
    climb_success_rate = (team_data['deepClimbAttempted'].astype(bool).sum() + team_data['shallowClimbAttempted'].astype(bool).sum()) / total_matches
    park_rate = team_data['parkAttempted'].astype(bool).sum() / total_matches
    
    # Calculate autonomous statistics
    auto_coral_l1 = team_data['autoCoralPlaceL1Count'].mean()
    auto_coral_l2 = team_data['autoCoralPlaceL2Count'].mean()
    auto_coral_l3 = team_data['autoCoralPlaceL3Count'].mean()
    auto_coral_l4 = team_data['autoCoralPlaceL4Count'].mean()
    auto_algae_net = team_data['autoAlgaePlaceNetShot'].mean()
    auto_algae_processor = team_data['autoAlgaePlaceProcessor'].mean()
    
    # Get team schedule
    schedule = get_team_schedule(team_number, CURRENT_EVENT_CODE, TBA_API_KEY)
    
    # Create schedule HTML
    schedule_html = ""
    if schedule:
        schedule_html = """
            <table class="schedule-table">
                <thead>
                    <tr>
                        <th>Match</th>
                        <th>Alliance</th>
                        <th>Alliance Partners</th>
                        <th>Opponents</th>
                        <th>Score</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for match in schedule:
            # Determine which alliance the team is on
            team_key = f'frc{team_number}'
            alliance_color = "Red" if team_key in match['alliances']['red']['team_keys'] else "Blue"
            alliance = match['alliances']['red' if alliance_color == "Red" else 'blue']
            
            # Get alliance partners and opponents
            alliance_partners = [team.replace('frc', '') for team in alliance['team_keys'] if team != team_key]
            opponents = [team.replace('frc', '') for team in match['alliances']['red']['team_keys'] + match['alliances']['blue']['team_keys'] 
                        if team != team_key and team not in alliance['team_keys']]
            
            # Format score
            score = f"{alliance['score']} - {match['alliances']['blue' if alliance_color == 'Red' else 'red']['score']}"
            
            # Determine result
            result = "W" if match['winning_alliance'] == alliance_color.lower() else "L"
            result_class = "win" if result == "W" else "loss"
            
            # Create team links
            partner_links = [f'<a href="team_{partner}.html">{partner}</a>' for partner in alliance_partners]
            opponent_links = [f'<a href="team_{opponent}.html">{opponent}</a>' for opponent in opponents]
            
            schedule_html += f"""
                <tr>
                    <td><a href="https://www.thebluealliance.com/match/{match['key']}" target="_blank">{match['key'].split('_')[-1]}</a></td>
                    <td>{alliance_color}</td>
                    <td>{', '.join(partner_links)}</td>
                    <td>{', '.join(opponent_links)}</td>
                    <td>{score}</td>
                    <td class="{result_class}">{result}</td>
                </tr>
            """
        
        schedule_html += """
                </tbody>
            </table>
        """
    
    # Create teleop scoring distribution chart
    teleop_fig = go.Figure(data=[
        go.Bar(name='L1', x=['Coral Scoring'], y=[avg_coral_l1]),
        go.Bar(name='L2', x=['Coral Scoring'], y=[avg_coral_l2]),
        go.Bar(name='L3', x=['Coral Scoring'], y=[avg_coral_l3]),
        go.Bar(name='L4', x=['Coral Scoring'], y=[avg_coral_l4]),
        go.Bar(name='Net Shot', x=['Algae Scoring'], y=[avg_algae_net]),
        go.Bar(name='Processor', x=['Algae Scoring'], y=[avg_algae_processor])
    ])
    
    # Update teleop layout
    teleop_fig.update_layout(
        title=f'Team {team_number} ({team_name}) Teleoperated Period Scoring Distribution',
        barmode='group',
        height=400
    )
    
    # Create autonomous scoring distribution chart
    auto_fig = go.Figure(data=[
        go.Bar(name='L1', x=['Coral Scoring'], y=[auto_coral_l1]),
        go.Bar(name='L2', x=['Coral Scoring'], y=[auto_coral_l2]),
        go.Bar(name='L3', x=['Coral Scoring'], y=[auto_coral_l3]),
        go.Bar(name='L4', x=['Coral Scoring'], y=[auto_coral_l4]),
        go.Bar(name='Net Shot', x=['Algae Scoring'], y=[auto_algae_net]),
        go.Bar(name='Processor', x=['Algae Scoring'], y=[auto_algae_processor])
    ])
    
    # Update autonomous layout
    auto_fig.update_layout(
        title=f'Team {team_number} ({team_name}) Autonomous Period Scoring Distribution',
        barmode='group',
        height=400
    )
    
    # Save the plots to separate files
    save_graph(teleop_fig, f'team_{team_number}_teleop.html')
    save_graph(auto_fig, f'team_{team_number}_auto.html')
    
    # remove the scouter scouterInitials column
    team_data = team_data.drop(columns=['scouterInitials'])
    # Create raw data table
    raw_data_table = team_data.to_html(
        index=False,
        classes='raw-data-table',
        float_format=lambda x: '{:.1f}'.format(x) if isinstance(x, float) else x
    )
    
    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Team {team_number} - {team_name} Scouting Data</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                flex: 1;
                margin-bottom: 60px;
            }}
            .team-header {{
                display: flex;
                align-items: center;
                gap: 20px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}
            .team-header h1 {{
                margin: 0;
            }}
            .team-name {{
                color: #7f8c8d;
                font-size: 1.2em;
            }}
            .team-rank {{
                background-color: #f8f9fa;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .tba-link {{
                margin-left: auto;
                padding: 8px 16px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                font-size: 0.9em;
                transition: background-color 0.2s;
            }}
            .tba-link:hover {{
                background-color: #0056b3;
            }}
            .statbotics-link {{
                margin-left: 10px;
                padding: 8px 16px;
                background-color: #28a745;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                font-size: 0.9em;
                transition: background-color 0.2s;
            }}
            .statbotics-link:hover {{
                background-color: #218838;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .stat-card {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                text-align: center;
            }}
            .stat-value {{
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }}
            .stat-label {{
                color: #7f8c8d;
                margin-top: 5px;
            }}
            .comments {{
                margin-top: 20px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
            }}
            .comment {{
                margin: 10px 0;
                padding: 10px;
                border-left: 4px solid #3498db;
                background-color: white;
            }}
            .graph-container {{
                margin: 20px 0;
                padding: 15px;
                background-color: white;
                border-radius: 6px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                overflow-x: auto;
            }}
            .schedule-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 14px;
                background-color: white;
                overflow-x: auto;
                display: block;
            }}
            .schedule-table th {{
                background-color: #f8f9fa;
                padding: 12px;
                text-align: left;
                border-bottom: 2px solid #dee2e6;
                position: sticky;
                top: 0;
                z-index: 1;
                white-space: nowrap;
            }}
            .schedule-table td {{
                padding: 8px 12px;
                border-bottom: 1px solid #dee2e6;
                white-space: nowrap;
            }}
            .schedule-table tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            .schedule-table tr:hover {{
                background-color: #f1f1f1;
            }}
            .schedule-table .win {{
                color: #27ae60;
                font-weight: bold;
            }}
            .schedule-table .loss {{
                color: #e74c3c;
                font-weight: bold;
            }}
            .raw-data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 14px;
                overflow-x: auto;
                display: block;
            }}
            .raw-data-table th {{
                background-color: #f8f9fa;
                padding: 12px;
                text-align: left;
                border-bottom: 2px solid #dee2e6;
                position: sticky;
                top: 0;
                z-index: 1;
                white-space: nowrap;
            }}
            .raw-data-table td {{
                padding: 8px 12px;
                border-bottom: 1px solid #dee2e6;
                white-space: nowrap;
            }}
            .raw-data-table tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            .raw-data-table tr:hover {{
                background-color: #f1f1f1;
            }}
            .raw-data-container {{
                margin-top: 40px;
                padding: 20px;
                background-color: white;
                border-radius: 6px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                display: none;
                overflow-x: auto;
            }}
            .toggle-button {{
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                background-color: #6c757d;
                color: white;
                cursor: pointer;
                transition: background-color 0.2s;
                margin-top: 20px;
                width: 100%;
                max-width: 200px;
            }}
            .toggle-button:hover {{
                background-color: #5a6268;
            }}
            .schedule-container {{
                margin-top: 40px;
                padding: 20px;
                background-color: white;
                border-radius: 6px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                overflow-x: auto;
            }}
            .bracket-container {{
                margin-top: 40px;
                padding: 20px;
                background-color: white;
                border-radius: 6px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                overflow-x: auto;
            }}
            .bracket-container h2 {{
                margin-bottom: 20px;
                color: #2c3e50;
                text-align: center;
            }}
            .bracket-wrapper {{
                display: flex;
                justify-content: space-between;
                padding: 20px 0;
                min-width: 1200px;
            }}
            .bracket-round {{
                display: flex;
                flex-direction: column;
                justify-content: space-around;
                margin: 0 20px;
                position: relative;
            }}
            .bracket-round:not(:last-child)::after {{
                content: '';
                position: absolute;
                top: 0;
                right: -20px;
                width: 20px;
                height: 100%;
                background: repeating-linear-gradient(
                    to right,
                    transparent,
                    transparent 10px,
                    #ccc 10px,
                    #ccc 20px
                );
                z-index: 1;
            }}
            .bracket-match {{
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                margin: 10px 0;
                min-width: 200px;
                position: relative;
                z-index: 2;
            }}
            .bracket-match.winner {{
                background-color: #e8f5e9;
                border-color: #4caf50;
            }}
            .bracket-match.loser {{
                background-color: #ffebee;
                border-color: #f44336;
            }}
            .bracket-team {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 5px;
            }}
            .bracket-team.winner {{
                font-weight: bold;
                color: #2e7d32;
            }}
            .bracket-team.loser {{
                color: #c62828;
            }}
            .bracket-score {{
                font-weight: bold;
                margin-left: 10px;
            }}
            .bracket-seed {{
                color: #666;
                font-size: 0.8em;
                margin-right: 5px;
            }}
            .bracket-round-title {{
                text-align: center;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
                text-transform: uppercase;
                font-size: 0.9em;
            }}
            .bracket-connector {{
                position: absolute;
                background-color: #ccc;
                z-index: 1;
            }}
            .bracket-connector.horizontal {{
                height: 2px;
            }}
            .bracket-connector.vertical {{
                width: 2px;
            }}
            .bracket-connector.winner {{
                background-color: #4caf50;
            }}
            .bracket-connector.loser {{
                background-color: #f44336;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background-color: white;
                border-top: 1px solid #e0e0e0;
                margin-top: 40px;
                font-size: 0.9em;
                color: #666;
                line-height: 1.5;
                box-shadow: 0 -2px 4px rgba(0,0,0,0.05);
            }}
            .footer a {{
                color: #007bff;
                text-decoration: none;
                transition: color 0.2s;
            }}
            .footer a:hover {{
                color: #0056b3;
                text-decoration: underline;
            }}
            .match-numbers {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 20px;
                font-size: 0.9em;
                color: #666;
            }}
            .match-numbers strong {{
                color: #2c3e50;
            }}
            .timestamp {{
                position: fixed;
                top: 10px;
                left: 10px;
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 0.8em;
                z-index: 1000;
            }}

            /* Mobile Responsive Styles */
            @media screen and (max-width: 768px) {{
                body {{
                    margin: 10px;
                }}
                .container {{
                    padding: 15px;
                }}
                .team-header {{
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 10px;
                }}
                .tba-link, .statbotics-link {{
                    margin-left: 0;
                    width: 100%;
                    text-align: center;
                }}
                .stats-grid {{
                    grid-template-columns: 1fr;
                }}
                .graph-container {{
                    padding: 10px;
                }}
                .schedule-table, .raw-data-table {{
                    font-size: 12px;
                }}
                .schedule-table th, .schedule-table td,
                .raw-data-table th, .raw-data-table td {{
                    padding: 6px 8px;
                }}
                .bracket-wrapper {{
                    min-width: 800px;
                }}
                .bracket-match {{
                    min-width: 150px;
                }}
                .bracket-round {{
                    margin: 0 10px;
                }}
                .bracket-round:not(:last-child)::after {{
                    right: -10px;
                    width: 10px;
                }}
                .footer {{
                    padding: 15px;
                    font-size: 0.8em;
                }}
            }}

            @media screen and (max-width: 480px) {{
                .team-header h1 {{
                    font-size: 1.5em;
                }}
                .team-name {{
                    font-size: 1em;
                }}
                .stat-value {{
                    font-size: 20px;
                }}
                .stat-label {{
                    font-size: 0.9em;
                }}
                .bracket-wrapper {{
                    min-width: 600px;
                }}
                .bracket-match {{
                    min-width: 120px;
                }}
                .bracket-team {{
                    font-size: 0.9em;
                }}
            }}
        </style>
        <script>
            function toggleRawData() {{
                const container = document.getElementById('rawDataContainer');
                const button = document.getElementById('toggleButton');
                if (container.style.display === 'none' || container.style.display === '') {{
                    container.style.display = 'block';
                    button.textContent = 'Hide Raw Data';
                }} else {{
                    container.style.display = 'none';
                    button.textContent = 'Show Raw Data';
                }}
            }}

            function createBracketConnectors() {{
                const rounds = document.querySelectorAll('.bracket-round');
                rounds.forEach((round, roundIndex) => {{
                    if (roundIndex < rounds.length - 1) {{
                        const matches = round.querySelectorAll('.bracket-match');
                        const nextRoundMatches = rounds[roundIndex + 1].querySelectorAll('.bracket-match');
                        
                        matches.forEach((match, matchIndex) => {{
                            const nextMatch = nextRoundMatches[Math.floor(matchIndex / 2)];
                            if (nextMatch) {{
                                const matchRect = match.getBoundingClientRect();
                                const nextMatchRect = nextMatch.getBoundingClientRect();
                                const roundRect = round.getBoundingClientRect();
                                
                                // Create vertical connector
                                const verticalConnector = document.createElement('div');
                                verticalConnector.className = 'bracket-connector vertical';
                                verticalConnector.style.height = (nextMatchRect.top - matchRect.bottom) + 'px';
                                verticalConnector.style.left = roundRect.right + 'px';
                                verticalConnector.style.top = matchRect.bottom + 'px';
                                
                                // Create horizontal connector
                                const horizontalConnector = document.createElement('div');
                                horizontalConnector.className = 'bracket-connector horizontal';
                                horizontalConnector.style.width = (nextMatchRect.left - roundRect.right) + 'px';
                                horizontalConnector.style.left = roundRect.right + 'px';
                                horizontalConnector.style.top = (nextMatchRect.top + nextMatchRect.height / 2) + 'px';
                                
                                // Add winner/loser classes
                                if (match.classList.contains('winner')) {{
                                    verticalConnector.classList.add('winner');
                                    horizontalConnector.classList.add('winner');
                                }} else {{
                                    verticalConnector.classList.add('loser');
                                    horizontalConnector.classList.add('loser');
                                }}
                                
                                document.body.appendChild(verticalConnector);
                                document.body.appendChild(horizontalConnector);
                            }}
                        }});
                    }}
                }});
            }}
            
            // Call the function after the page loads
            window.addEventListener('load', createBracketConnectors);
        </script>
    </head>
    <body>
        <div class="container">
            <div class="team-header">
                <h1>Team {team_number}</h1>
                <div class="team-name">{team_name}</div>
                <div class="team-rank">{rank_text}</div>
                <a href="https://www.thebluealliance.com/team/{team_number}" target="_blank" class="tba-link">View on Blue Alliance</a>
                <a href="https://statbotics.io/team/{team_number}/2025" target="_blank" class="statbotics-link">View on Statbotics</a>
            </div>
            
            <div class="match-numbers">
                <strong>Matches Scouted:</strong> {', '.join(sorted(team_data['matchNumber'].astype(str)))}
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_matches}</div>
                    <div class="stat-label">Total Matches</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{endgame_points:.1f}</div>
                    <div class="stat-label">Avg Endgame Points</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{climb_success_rate:.1%}</div>
                    <div class="stat-label">Climb Success Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{park_rate:.1%}</div>
                    <div class="stat-label">Park Rate</div>
                </div>
            </div>

            <div class="graph-container">
                <h2>Teleoperated Period</h2>
                <iframe src="graphs/team_{team_number}_teleop.html" style="width: 100%; height: 400px; border: none;"></iframe>
            </div>

            <div class="graph-container">
                <h2>Autonomous Period</h2>
                <iframe src="graphs/team_{team_number}_auto.html" style="width: 100%; height: 400px; border: none;"></iframe>
            </div>

            <div class="schedule-container">
                <h2>Event Schedule</h2>
                {schedule_html}
            </div>

            <div class="comments">
                <h2>Match Comments</h2>
                {''.join([f'<div class="comment">{comment}</div>' for comment in team_data['comment'].dropna()])}
            </div>

            <button id="toggleButton" class="toggle-button" onclick="toggleRawData()">Show Raw Data</button>
            <div id="rawDataContainer" class="raw-data-container">
                <h2>Raw Match Data</h2>
                {raw_data_table}
            </div>
        </div>
        <div class="footer">
            Data collected and organized by FRC7414<br>
            Visualization and site created and maintained by FRC272<br>
            Data further enriched by <a href="https://www.thebluealliance.com" target="_blank">The Blue Alliance</a> and <a href="https://statbotics.io" target="_blank">Statbotics</a><br><br>
            Contact: <a href="mailto:jake.gads@gmail.com">jake.gads@gmail.com</a>
        </div>
    </body>
    </html>
    """
    
    # Create output directory if it doesn't exist
    output_dir = Path('team_pages')
    output_dir.mkdir(exist_ok=True)
    
    # Save the HTML file
    with open(output_dir / f'team_{team_number}.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def get_playoff_bracket(event_code: str, api_key: str) -> dict:
    """Fetch playoff bracket data from The Blue Alliance API"""
    headers = {'X-TBA-Auth-Key': api_key}
    base_url = 'https://www.thebluealliance.com/api/v3'
    
    try:
        # Get the playoff bracket HTML
        response = requests.get(
            f'https://www.thebluealliance.com/event/{event_code}#results'
        )
        
        if response.status_code == 200:
            # Parse HTML with BeautifulSoup
            soup = bs4.BeautifulSoup(response.text, 'html.parser')
            
            # Find the bracket div
            bracket_div = soup.find('div', id='double-elim-bracket-wrapper')
            if not bracket_div:
                print("Could not find playoff bracket div")
                return {'html': "", 'css': ""}
                
            # Find all style tags and combine their contents
            styles = soup.find_all('style')
            css = '\n'.join(style.string for style in styles) if styles else ''
            html = bracket_div.prettify()
            return {'html': html, 'css': ''}
            
        else:
            print(f"Error fetching playoff bracket: {response.status_code}")
            return {'html': "", 'css': ""}
            
    except Exception as e:
        print(f"Error fetching playoff bracket: {e}")
        return {'html': "", 'css': ""}

def create_index_page(teams, team_names):
    """Create an index page listing all teams."""
    # Get current timestamp
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get playoff bracket data
    bracket_data = get_playoff_bracket(CURRENT_EVENT_CODE, TBA_API_KEY)
    
    # Get event rankings
    rankings = get_event_rankings(CURRENT_EVENT_CODE, TBA_API_KEY)
    
    # Read the CSV file to get scoring data
    df = pd.read_csv('VScouterData.csv')
    
    # Calculate average scores for each team
    team_scores = {}
    for team in teams:
        team_data = df[df['selectTeam'] == team]
        # Calculate endgame points - only count the highest scoring action per match
        endgame_points = team_data.apply(lambda row: 
            max([
                12 if row['deepClimbAttempted'] and not row['climbFailed'] else 0,  # Deep climb is worth 12 points
                6 if row['shallowClimbAttempted'] and not row['climbFailed'] else 0,  # Shallow climb is worth 6 points
                2 if row['parkAttempted'] else 0  # Park is worth 2 points
            ]), 
            axis=1
        ).mean()
        team_scores[team] = {
            'coral': (team_data['autoCoralPlaceL1Count'].mean() * 3+ 
                    team_data['autoCoralPlaceL2Count'].mean() * 4 +
                    team_data['autoCoralPlaceL3Count'].mean() * 6 +
                    team_data['autoCoralPlaceL4Count'].mean() * 7) +  # Double auto coral
                    team_data['teleopCoralPlaceL1Count'].mean() * 2+ 
                    team_data['teleopCoralPlaceL2Count'].mean() * 3 +
                    team_data['teleopCoralPlaceL3Count'].mean() * 4 +
                    team_data['teleopCoralPlaceL4Count'].mean() * 5,
            'algae': (team_data['autoAlgaePlaceNetShot'].mean() * 6 +
                    team_data['autoAlgaePlaceProcessor'].mean() * 4) +  # Double auto algae
                    team_data['teleopAlgaePlaceNetShot'].mean() * 6 +
                    team_data['teleopAlgaePlaceProcessor'].mean() * 4,
            'endgame': endgame_points
        }
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{CURRENT_EVENT_CODE} Scouting Data Index</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                flex: 1;
            }}
            .controls {{
                margin-bottom: 20px;
                display: flex;
                gap: 20px;
                align-items: center;
                flex-wrap: wrap;
            }}
            .search-box {{
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 200px;
            }}
            .hide-teams {{
                display: flex;
                gap: 10px;
                align-items: center;
            }}
            .hide-teams input {{
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 150px;
            }}
            .hide-teams button {{
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                background-color: #f8f9fa;
                cursor: pointer;
                transition: background-color 0.2s;
            }}
            .hide-teams button:hover {{
                background-color: #e9ecef;
            }}
            .sort-buttons {{
                display: flex;
                gap: 10px;
            }}
            .sort-button {{
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                background-color: #f8f9fa;
                cursor: pointer;
                transition: background-color 0.2s;
            }}
            .sort-button:hover {{
                background-color: #e9ecef;
            }}
            .sort-button.active {{
                background-color: #007bff;
                color: white;
            }}
            .info-button {{
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                background-color: #17a2b8;
                color: white;
                cursor: pointer;
                transition: background-color 0.2s;
            }}
            .info-button:hover {{
                background-color: #138496;
            }}
            .modal {{
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
            }}
            .modal-content {{
                background-color: white;
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                padding: 20px;
                border-radius: 8px;
                width: 80%;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
            }}
            .close {{
                position: absolute;
                right: 20px;
                top: 10px;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }}
            .close:hover {{
                color: #666;
            }}
            .scoring-info {{
                margin-top: 20px;
            }}
            .scoring-info h3 {{
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            .scoring-info p {{
                margin: 10px 0;
                line-height: 1.5;
            }}
            .scoring-info ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .scoring-info li {{
                margin: 5px 0;
            }}
            .team-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }}
            .team-card {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                text-decoration: none;
                color: #2c3e50;
                transition: transform 0.2s;
            }}
            .team-card:hover {{
                transform: translateY(-2px);
            }}
            .team-number {{
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .team-name {{
                color: #7f8c8d;
                font-size: 0.9em;
                margin-bottom: 5px;
            }}
            .team-stats {{
                font-size: 0.9em;
                color: #666;
            }}
            .team-rank {{
                font-weight: bold;
                color: #2c3e50;
                margin: 5px 0;
                padding: 4px 8px;
                background-color: #e9ecef;
                border-radius: 4px;
                display: inline-block;
            }}
            .bracket-container {{
                margin-top: 40px;
                padding: 20px;
                background-color: white;
                border-radius: 6px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                overflow-x: auto;
            }}
            .bracket-container h2 {{
                margin-bottom: 20px;
                color: #2c3e50;
                text-align: center;
            }}
            .bracket-wrapper {{
                display: flex;
                justify-content: space-between;
                padding: 20px 0;
                min-width: 1200px;
            }}
            .bracket-round {{
                display: flex;
                flex-direction: column;
                justify-content: space-around;
                margin: 0 20px;
                position: relative;
            }}
            .bracket-round:not(:last-child)::after {{
                content: '';
                position: absolute;
                top: 0;
                right: -20px;
                width: 20px;
                height: 100%;
                background: repeating-linear-gradient(
                    to right,
                    transparent,
                    transparent 10px,
                    #ccc 10px,
                    #ccc 20px
                );
                z-index: 1;
            }}
            .bracket-match {{
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                margin: 10px 0;
                min-width: 200px;
                position: relative;
                z-index: 2;
            }}
            .bracket-match.winner {{
                background-color: #e8f5e9;
                border-color: #4caf50;
            }}
            .bracket-match.loser {{
                background-color: #ffebee;
                border-color: #f44336;
            }}
            .bracket-team {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 5px;
            }}
            .bracket-team.winner {{
                font-weight: bold;
                color: #2e7d32;
            }}
            .bracket-team.loser {{
                color: #c62828;
            }}
            .bracket-score {{
                font-weight: bold;
                margin-left: 10px;
            }}
            .bracket-seed {{
                color: #666;
                font-size: 0.8em;
                margin-right: 5px;
            }}
            .bracket-round-title {{
                text-align: center;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
                text-transform: uppercase;
                font-size: 0.9em;
            }}
            .bracket-connector {{
                position: absolute;
                background-color: #ccc;
                z-index: 1;
            }}
            .bracket-connector.horizontal {{
                height: 2px;
            }}
            .bracket-connector.vertical {{
                width: 2px;
            }}
            .bracket-connector.winner {{
                background-color: #4caf50;
            }}
            .bracket-connector.loser {{
                background-color: #f44336;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                background-color: white;
                border-top: 1px solid #e0e0e0;
                margin-top: 40px;
                font-size: 0.9em;
                color: #666;
                line-height: 1.5;
                box-shadow: 0 -2px 4px rgba(0,0,0,0.05);
            }}
            .footer a {{
                color: #007bff;
                text-decoration: none;
                transition: color 0.2s;
            }}
            .footer a:hover {{
                color: #0056b3;
                text-decoration: underline;
            }}
            .timestamp {{
                position: fixed;
                top: 10px;
                left: 10px;
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 0.8em;
                z-index: 1000;
            }}

            /* Mobile Responsive Styles */
            @media screen and (max-width: 768px) {{
                body {{
                    margin: 10px;
                }}
                .container {{
                    padding: 15px;
                }}
                .controls {{
                    flex-direction: column;
                    gap: 15px;
                }}
                .search-box {{
                    width: 100%;
                }}
                .hide-teams {{
                    width: 100%;
                }}
                .hide-teams input {{
                    width: calc(100% - 100px);
                }}
                .sort-buttons {{
                    flex-wrap: wrap;
                    justify-content: center;
                    gap: 8px;
                }}
                .sort-button, .info-button {{
                    flex: 1;
                    min-width: 150px;
                }}
                .team-grid {{
                    grid-template-columns: 1fr;
                }}
                .team-card {{
                    padding: 12px;
                }}
                .team-number {{
                    font-size: 1.1em;
                }}
                .team-name {{
                    font-size: 0.85em;
                }}
                .team-stats {{
                    font-size: 0.85em;
                }}
                .bracket-wrapper {{
                    min-width: 800px;
                }}
                .bracket-match {{
                    min-width: 150px;
                }}
                .bracket-round {{
                    margin: 0 10px;
                }}
                .bracket-round:not(:last-child)::after {{
                    right: -10px;
                    width: 10px;
                }}
                .modal-content {{
                    width: 95%;
                    padding: 15px;
                }}
                .scoring-info {{
                    font-size: 0.9em;
                }}
                .footer {{
                    padding: 15px;
                    font-size: 0.8em;
                }}
            }}

            @media screen and (max-width: 480px) {{
                .team-number {{
                    font-size: 1em;
                }}
                .team-name {{
                    font-size: 0.8em;
                }}
                .team-stats {{
                    font-size: 0.8em;
                }}
                .bracket-wrapper {{
                    min-width: 600px;
                }}
                .bracket-match {{
                    min-width: 120px;
                }}
                .bracket-team {{
                    font-size: 0.9em;
                }}
                .sort-button, .info-button {{
                    min-width: 120px;
                    font-size: 0.9em;
                }}
                .modal-content {{
                    padding: 10px;
                }}
                .scoring-info {{
                    font-size: 0.85em;
                }}
                .scoring-info ul {{
                    padding-left: 15px;
                }}
            }}
        </style>
        <script>
            function filterTeams() {{   
                const searchBox = document.getElementById('teamSearch');
                const filter = searchBox.value.toLowerCase();
                const cards = document.getElementsByClassName('team-card');
                
                for (let card of cards) {{
                    const teamNumber = card.querySelector('.team-number').textContent.toLowerCase();
                    if (teamNumber.includes(filter)) {{
                        card.style.display = '';
                    }} else {{
                        card.style.display = 'none';
                    }}
                }}
            }}
            
            function hideTeams() {{
                const hideInput = document.getElementById('hideTeams');
                const teamsToHide = hideInput.value.split(',').map(num => num.trim());
                const cards = document.getElementsByClassName('team-card');
                
                for (let card of cards) {{
                    const teamNumber = card.querySelector('.team-number').textContent.split(' ')[1];
                    if (teamsToHide.includes(teamNumber)) {{
                        card.style.display = 'none';
                    }}
                }}
            }}
            
            function showAllTeams() {{
                const hideInput = document.getElementById('hideTeams');
                hideInput.value = '';
                const cards = document.getElementsByClassName('team-card');
                
                for (let card of cards) {{
                    card.style.display = '';
                }}
            }}
            
            function sortTeams(criteria) {{
                const container = document.querySelector('.team-grid');
                const cards = Array.from(container.getElementsByClassName('team-card'));
                const buttons = document.getElementsByClassName('sort-button');
                
                // Update active button
                for (let button of buttons) {{
                    button.classList.remove('active');
                }}
                event.target.classList.add('active');
                
                // Sort cards
                cards.sort((a, b) => {{
                    if (criteria === 'number') {{
                        const aNum = parseInt(a.querySelector('.team-number').textContent.split(' ')[1]);
                        const bNum = parseInt(b.querySelector('.team-number').textContent.split(' ')[1]);
                        return aNum - bNum;
                    }} else if (criteria === 'rank') {{
                        const aRank = parseInt(a.dataset.rank);
                        const bRank = parseInt(b.dataset.rank);
                        return aRank - bRank;
                    }} else {{
                        const aValue = parseFloat(a.dataset[criteria]);
                        const bValue = parseFloat(b.dataset[criteria]);
                        return bValue - aValue;
                    }}
                }});
                
                // Reorder cards
                cards.forEach(card => container.appendChild(card));
            }}
            
            function showInfo() {{
                document.getElementById('infoModal').style.display = 'block';
            }}
            
            function hideInfo() {{
                document.getElementById('infoModal').style.display = 'none';
            }}
            
            // Close modal when clicking outside
            window.onclick = function(event) {{
                const modal = document.getElementById('infoModal');
                if (event.target == modal) {{
                    modal.style.display = 'none';
                }}
            }}
        </script>
    </head>
    <body>
        <div class="timestamp">Last updated: {current_time}</div>
        <div class="container">
            <h1>{CURRENT_EVENT_CODE} Scouting Data</h1>
            <div class="controls">
                <input type="text" id="teamSearch" class="search-box" placeholder="Filter by team number..." onkeyup="filterTeams()">
                <div class="hide-teams">
                    <input type="text" id="hideTeams" class="search-box" placeholder="Hide teams (comma-separated)" onkeyup="hideTeams()">
                    <button onclick="showAllTeams()">Show All</button>
                </div>
                <div class="sort-buttons">
                    <button class="sort-button" onclick="sortTeams('number')">Sort by Team Number</button>
                    <button class="sort-button" onclick="sortTeams('rank')">Sort by Rank</button>
                    <button class="sort-button" onclick="sortTeams('coral')">Sort by Coral</button>
                    <button class="sort-button" onclick="sortTeams('algae')">Sort by Algae</button>
                    <button class="sort-button" onclick="sortTeams('endgame')">Sort by Endgame</button>
                    <button class="info-button" onclick="showInfo()">Info</button>
                </div>
            </div>
            <div class="team-grid">
    """
    
    for team in sorted(teams):
        team_name = team_names.get(team, f'Team {team}')
        scores = team_scores[team]
        html_content += f"""
                <a href="team_{team}.html" class="team-card" data-coral="{scores['coral']:.1f}" data-algae="{scores['algae']:.1f}" data-endgame="{scores['endgame']:.1f}" data-rank="{rankings.get(team, {}).get('rank', 999999)}">
                    <div class="team-number">Team {team}</div>
                    <div class="team-name">{team_name}</div>
                    <div class="team-rank">Rank: {rankings.get(team, {}).get('rank', 'N/A')}</div>
                    <div class="team-stats">
                        Coral: {scores['coral']:.1f} | Algae: {scores['algae']:.1f} | Endgame: {scores['endgame']:.1f}
                    </div>
                </a>
        """
    
    html_content += """
            </div>
    """
    
    # Add playoff bracket if available
    if bracket_data['html']:
        html_content += f"""
            <div class="bracket-container">
                <h2>Playoff Bracket</h2>
                <div class="bracket-wrapper">
                    {bracket_data['html']}
                </div>
            </div>
        """
    
    html_content += """
        </div>

        <div id="infoModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="hideInfo()">&times;</span>
                <h2>Scoring Calculations</h2>
                <div class="scoring-info">
                    <h3>Coral Scoring</h3>
                    <p>The coral score is calculated as a weighted sum of coral placements:</p>
                    <ul>
                        <li>Autonomous Period:</li>
                        <ul>
                            <li>Level 1: 3 points per coral</li>
                            <li>Level 2: 4 points per coral</li>
                            <li>Level 3: 6 points per coral</li>
                            <li>Level 4: 7 points per coral</li>
                        </ul>
                        <li>Teleoperated Period:</li>
                        <ul>
                            <li>Level 1: 2 points per coral</li>
                            <li>Level 2: 3 points per coral</li>
                            <li>Level 3: 4 points per coral</li>
                            <li>Level 4: 5 points per coral</li>
                        </ul>
                    </ul>
                    <p>Formula: (Auto L1×3 + Auto L2×4 + Auto L3×6 + Auto L4×7) + (Teleop L1×2 + Teleop L2×3 + Teleop L3×4 + Teleop L4×5)</p>
                    
                    <h3>Algae Scoring</h3>
                    <p>The algae score has the same weights for both autonomous and teleoperated periods:</p>
                    <ul>
                        <li>Autonomous Period:</li>
                        <ul>
                            <li>Net Shot: 6 points per algae</li>
                            <li>Processor: 4 points per algae</li>
                        </ul>
                        <li>Teleoperated Period:</li>
                        <ul>
                            <li>Net Shot: 6 points per algae</li>
                            <li>Processor: 4 points per algae</li>
                        </ul>
                    </ul>
                    <p>Formula: (Auto Net Shot×6 + Auto Processor×4) + (Teleop Net Shot×6 + Teleop Processor×4)</p>

                    <h3>Endgame Scoring</h3>
                    <p>The endgame score is calculated from the final actions of the match:</p>
                    <ul>
                        <li>Park: 2 points</li>
                        <li>Climb: 12 points (shallow climbs are not denoted)</li>
                    </ul>
                    <p>Note: A team can only score one endgame action per match.</p>
                    
                    <p><em>Note: All scores shown are averages per match.</em></p>
                </div>
            </div>
        </div>
        <div class="footer">
            Data collected and organized by FRC7414<br>
            Visualization and site created and maintained by FRC272<br>
            Data further enriched by <a href="https://www.thebluealliance.com" target="_blank">The Blue Alliance</a> and <a href="https://statbotics.io" target="_blank">Statbotics</a><br><br>
            Contact: <a href="mailto:jake.gads@gmail.com">jake.gads@gmail.com</a>
        </div>
    </body>
    </html>
    """
    
    # Save the index file
    with open('team_pages/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    # Read the CSV file with boolean columns properly handled
    boolean_columns = ['deepClimbAttempted', 'shallowClimbAttempted', 'parkAttempted', 'climbFailed', 'playedDefense', 'brokeDown']
    df = pd.read_csv('VScouterData.csv', dtype={col: str for col in boolean_columns})
    
    # Convert boolean columns to actual boolean values
    for col in boolean_columns:
        df[col] = df[col].str.lower() == 'true'
    
    # Get unique teams
    teams = df['selectTeam'].unique()
    
    # Get team names from TBA
    team_names = get_tba_team_names(teams, TBA_API_KEY)
    
    # Get event rankings
    rankings = get_event_rankings(CURRENT_EVENT_CODE, TBA_API_KEY)
    
    # Create pages for each team
    for team in teams:
        team_data = df[df['selectTeam'] == team]
        create_team_page(team_data, team, team_names.get(team, f'Team {team}'), rankings)
    
    # Create index page
    create_index_page(teams, team_names)
    
    print(f"Generated pages for {len(teams)} teams in the 'team_pages' directory.")
    print("Open 'team_pages/index.html' to view the results.")
    

if __name__ == "__main__":
    main()
    # Open the index file in the default web browser
    webbrowser.open('file://' + os.path.abspath('team_pages/index.html'))