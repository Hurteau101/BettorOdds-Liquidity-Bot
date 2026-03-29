import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from discordwebhook import Discord
from team_mapper import nfl_team_map, ncaa_team_map, cbb_team_map


class DiscordBot:
    def __init__(self, league):
        load_dotenv()
        self.league = league

        self.webhook = self._webhook_mapper(league)
        self.discord = Discord(url=self.webhook)

    def _webhook_mapper(self, league):
        MAPPER = {
            "nfl": os.getenv("DISCORD_WEBHOOK_URL_NFL"),
            "ncaaf": os.getenv("DISCORD_WEBHOOK_URL_NCAAF"),
            "nba": os.getenv("DISCORD_WEBHOOK_URL_NBA"),
            "nhl": os.getenv("DISCORD_WEBHOOK_URL_NHL"),
            "ncaab": os.getenv("DISCORD_WEBHOOK_URL_NCAAB"),
            "ufc": os.getenv("DISCORD_WEBHOOK_URL_UFC"),
            "mlb": os.getenv("DISCORD_WEBHOOK_URL_MLB"),
        }

        if league.lower() not in MAPPER:
            raise ValueError(f"League '{league}' is not supported. Supported leagues: {list(MAPPER.keys())}")

        return MAPPER.get(league.lower(), os.getenv("DISCORD_WEBHOOK_URL"))


    def player_message(self, data, stat_type, line):
        player_name = data.get("additional_data").get("player_name")
        return f"{player_name} ({str(line)})"

    def game_message(self, data, stat_type, line):
        league_mapper = {
            "NFL": nfl_team_map,
            "NCAAF": ncaa_team_map,
            "NCAAB": cbb_team_map,
        }


        mapper = league_mapper.get(self.league.upper(), {})

        bet_info = data.get("additional_data", {}).get("bet_info")
        if stat_type == "Spread":
            liquidity = data.get("liquidity", {})
            highest = max(
                liquidity.values(),
                key=lambda x: x["highest_order"]["total_liquidity"]
            )["highest_order"]

            # bet_info = stat_type
            team_split = highest.get('side').split(" ")
            if len(team_split) <= 2:
                spread_value = team_split[1]
            else:
                spread_value = team_split[-1]

            # team_name = team_split[0]
            # renamed_team = mapper.get(team_name.upper(), team_name)
            # bet_info = f"{stat_type} {' '.join(team_split[1:])}"
            bet_info = f"{stat_type} {spread_value}"


        elif stat_type == "Moneyline":
            # team_name = bet_info
            # renamed_team = mapper.get(team_name.upper(), team_name)
            # bet_info = renamed_team
            bet_info = stat_type
        elif stat_type == "Total" or stat_type == "Total Rounds":
            bet_info = str(line)
        elif stat_type == "Team Total":
            team_split = bet_info.split(" ")
            team_name = team_split[2:]
            team_name = " ".join(team_name)
            renamed_team = mapper.get(team_name.upper(), team_name)
            bet_info = f"{renamed_team} ({str(line)})"

        return bet_info

        # return f"{bet_info.upper() if not None else ''} [{stat_type}]"

    def discord_message(self, data, market_changed=False):
        stat_type = data.get("additional_data").get("stat_type")
        line = data.get("additional_data").get("line")

        game_start_utc_str = data.get("additional_data").get("game_start_time")
        if game_start_utc_str:
            game_start_utc = datetime.fromisoformat(game_start_utc_str)
            eastern = ZoneInfo("America/New_York")
            game_start_eastern = game_start_utc.astimezone(eastern)
            game_start_time = game_start_eastern.strftime("%Y-%m-%d")
        else:
            game_start_time = "N/A"

        if data.get("additional_data", {}).get("type") == "player":
            main_title = self.player_message(data, stat_type, line)
        else:
            main_title = self.game_message(data, stat_type, line)


        notification = self.create_notification(main_title, game_start_time, data, market_changed, stat_type)

        self.discord.post(embeds=[notification])

    @staticmethod
    def format_odds(value: int | float) -> str:
        if value > 0:
            return f"+{value}"
        return str(value)

    # def create_notification(self, main_title, start_time, market_data, market_change, stat_type):
    #     fields = []
    #
    #     previous_message = "*(Play was sent previously but market moved +/- 1500)*\n" if market_change else ""
    #
    #     over_data = market_data.get("liquidity", {}).get("over", {}).get("highest_order", {})
    #     under_data = market_data.get("liquidity", {}).get("under", {}).get("highest_order", {})
    #
    #
    #
    #     highest = max(
    #         market_data["liquidity"].values(),
    #         key=lambda x: x["highest_order"]["total_liquidity"]
    #     )["highest_order"]
    #
    #     fields.append({
    #         "name": "",
    #         "value": f"**Stat Type:** {stat_type}",
    #         "inline": False
    #     })
    #
    #     fields.append({
    #         "name": "Game Details",
    #         "value": f"{previous_message}"
    #                  f"**Event:**  {market_data.get('additional_data').get('game_title')}\n"
    #                  f"**Date:** {start_time}\n",
    #     })
    #
    #     if stat_type == "Moneyline" or stat_type == "Spread":
    #         pass
    #     else:
    #         fields.append({
    #             "name": "Liquidity Quick Summary",
    #             "value": f"```\nTotal Over: ${over_data.get('total_liquidity', 0)} "
    #                      f"\nCost Avg Odds: {DiscordBot.format_odds(over_data.get('cost_avg_odds', 0))}\n\n"
    #                      f"Total Under: ${under_data.get('total_liquidity', 0)}"
    #                      f"\nCost Avg Odds: {DiscordBot.format_odds(under_data.get('cost_avg_odds', 0))}\n\n"
    #                      f"Highest Order: ${highest.get('liquidity_left', 0)} [{highest.get('side').title()}]\n"
    #                      f"Highest Order Odds: {DiscordBot.format_odds(highest.get('american_price', 0))}\n```",
    #             "inline": False
    #         })
    #
    #     link_fields = [
    #         {
    #             "name": f"{order_data.get('side').title()} {market_data.get('additional_data').get('line')} Link",
    #             "value": f"**↠** [Mobile]({order_data.get('mobile_link')}) | [Desktop]({order_data.get('desktop_link')})",
    #             "inline": False
    #         }
    #         for side, data in market_data.get("liquidity", {}).items()
    #         if (order_data := data.get("highest_order"))
    #     ]
    #
    #     fields.extend(link_fields)
    #
    #     return {
    #         "title": main_title,
    #         "color": 0x5D3A9B,
    #         "author": {
    #             "name": f"Novig Bot",
    #         },
    #         "footer": {
    #             "text": "V2.0.0\n"
    #                     "Powered by BettorOdds"
    #         },
    #         "fields": fields,
    #         "timestamp": datetime.now(timezone.utc).isoformat()
    #     }

    def create_notification(self, main_title, start_time, market_data, market_change, stat_type):
        fields = []

        previous_message = "*(Play was sent previously but market moved +/- 1500)*\n" if market_change else ""

        liquidity = market_data.get("liquidity", {})
        sides = list(liquidity.keys())

        # Moneyline / Spread
        if stat_type in ("Moneyline", "Spread"):
            side_1_name, side_2_name = sides[0], sides[1]
            side_1_data = liquidity.get(side_1_name, {}).get("highest_order", {})
            side_2_data = liquidity.get(side_2_name, {}).get("highest_order", {})
        # Totals (always over/under)
        else:
            side_1_name, side_2_name = "over", "under"
            side_1_data = liquidity.get("over", {}).get("highest_order", {})
            side_2_data = liquidity.get("under", {}).get("highest_order", {})


        # Find the overall highest order
        highest = max(
            liquidity.values(),
            key=lambda x: x["highest_order"]["total_liquidity"]
        )["highest_order"]

        fields.append({
            "name": "",
            "value": f"**Stat Type:** {stat_type}",
            "inline": False
        })

        fields.append({
            "name": "Game Details",
            "value": f"{previous_message}"
                     f"**Event:**  {market_data.get('additional_data', {}).get('game_title')}\n"
                     f"**Date:** {start_time}\n",
        })

       # Liquidity summary depends on stat_type
        fields.append({
            "name": "Liquidity Quick Summary",
            "value": f"```\n{side_1_name.upper() if stat_type in ['Moneyline', 'Spread'] else side_1_name.title()}: ${side_1_data.get('total_liquidity', 0)} "
                     f"\nCost Avg Odds: {DiscordBot.format_odds(side_1_data.get('cost_avg_odds', 0))}\n\n"
                     f"{side_2_name.upper() if stat_type in ['Moneyline', 'Spread'] else side_2_name.title()}: ${side_2_data.get('total_liquidity', 0)}"
                     f"\nCost Avg Odds: {DiscordBot.format_odds(side_2_data.get('cost_avg_odds', 0))}\n\n"
                     f"Highest Order: ${highest.get('liquidity_left', 0)} [{highest.get('side').title()}]\n"
                     f"Highest Order Odds: {DiscordBot.format_odds(highest.get('american_price', 0))}\n```",
            "inline": False
        })

        # Links for each side
        link_fields = [
            {
                "name": (
                    f"{order_data.get('side').upper()} Link"
                    if stat_type in ("Moneyline", "Spread")
                    else f"{order_data.get('side').title()} {market_data.get('additional_data', {}).get('line')} Link"
                ),
                "value": f"**↠** [Mobile]({order_data.get('mobile_link')}) | [Desktop]({order_data.get('desktop_link')})",
                # "value": f"**↠** [Desktop]({order_data.get('desktop_link')})",
                "inline": False
            }
            for side, data in liquidity.items()
            if (order_data := data.get("highest_order"))
        ]

        fields.extend(link_fields)

        return {
            "title": main_title,
            "color": 0x5D3A9B,
            "author": {"name": "Novig Bot"},
            "footer": {"text": "V2.0.1\nPowered by BettorOdds"},
            "fields": fields,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


