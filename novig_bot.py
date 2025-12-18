from novig import Novig
import json

from process_manager import ProcessManager


class NovigSender:
    def __init__(self, filter_data, difference_amount):
        self.filters = filter_data
        self.amount = difference_amount


    async def runner(self):
        total_difference_filter = {
            "filter_type": "total_difference",
            "difference_amount": self.amount
        }

        novig = Novig(filters=self.filters, filter_amount_dict=total_difference_filter)
        return await novig.run()



if __name__ == "__main__":
    # import asyncio
    # raw = asyncio.run(Novig.get_raw_data(["NCAAF"]))
    # import json
    #
    # with open("raw.json", "w") as f:
    #     json.dump(raw, f, indent=4)

    import asyncio

    async def main():
        with open("nfl_filters.json", "r") as f:
            nfl_data = json.load(f)
            nfl_mainlines = {"NFL": nfl_data.get("NFL", {}).get("NFL_Mainlines")}
            nfl_props = {"NFL": nfl_data.get("NFL", {}).get("NFL_Props")}

        with open("ncaaf_filters.json", "r") as f:
            ncaaf_filters = json.load(f)

        with open("ncaab.json", "r") as f:
            ncaab_filters = json.load(f)

        with open("nba_filters.json", "r") as f:
            nba_data = json.load(f)
            nba_mainlines = {"NBA": nba_data.get("NBA", {}).get("NBA_Mainlines")}
            nba_props = {"NBA": nba_data.get("NBA", {}).get("NBA_Props")}

        with open("nhl_filters.json", "r") as f:
            nhl_filters = json.load(f)
            nhl_mainlines = {"NHL": nhl_filters.get("NHL", {}).get("NHL_Mainlines")}
            nhl_props = {"NHL": nhl_filters.get("NHL", {}).get("NHL_Props")}

        with open("ufc_filters.json", "r") as f:
            ufc_filters = json.load(f)
            ufc_mainlines = {"UFC": ufc_filters.get("UFC", {}).get("UFC_Mainlines")}
            ufc_alternates = {"UFC": ufc_filters.get("UFC", {}).get("UFC_Alternates")}

        sender_nba_mainline = NovigSender(filter_data=nba_mainlines, difference_amount=5000)
        sender_nba_props = NovigSender(filter_data=nba_props, difference_amount=3000)

        sender_nhl_mainline = NovigSender(filter_data=nhl_mainlines, difference_amount=5000)
        sender_nhl_props = NovigSender(filter_data=nhl_props, difference_amount=3000)

        sender_nfl_mainline = NovigSender(filter_data=nfl_mainlines, difference_amount=3000)
        sender_nfl_props = NovigSender(filter_data=nfl_props, difference_amount=3000)

        sender_ncaaf = NovigSender(filter_data=ncaaf_filters, difference_amount=4000)

        sender_ncaab = NovigSender(filter_data=ncaab_filters, difference_amount=4000)

        sender_ufc_mainlines = NovigSender(filter_data=ufc_mainlines, difference_amount=7000)
        sender_ufc_alternates = NovigSender(filter_data=ufc_alternates, difference_amount=5000)

        nfl_mainline_data, nfl_props_data, ncaaf_data, nba_mainline_data, nba_props_data, nhl_mainline_data, nhl_props_data, ncaab_mainline_data, ufc_mainline_data, ufc_alternate_data = await asyncio.gather(
            sender_nfl_mainline.runner(),
            sender_nfl_props.runner(),
            sender_ncaaf.runner(),
            sender_nba_mainline.runner(),
            sender_nba_props.runner(),
            sender_nhl_mainline.runner(),
            sender_nhl_props.runner(),
            sender_ncaab.runner(),
            sender_ufc_mainlines.runner(),
            sender_ufc_alternates.runner(),
        )

        nfl_manager = ProcessManager(redis_database=8, difference_amount=1500, league="NFL")
        ncaaf_manager = ProcessManager(redis_database=9, difference_amount=1500, league="NCAAF")

        nba_manager = ProcessManager(redis_database=10, difference_amount=1500, league="NBA")

        nhl_manager = ProcessManager(redis_database=11, difference_amount=1500, league="NHL")

        nfl_manager.manger(nfl_mainline_data["NFL"], "NFL")
        nfl_manager.manger(nfl_props_data["NFL"], "NFL")

        ncaaf_manager.manger(ncaaf_data["NCAAF"], "NCAAF")

        nba_manager.manger(nba_mainline_data["NBA"], "NBA")
        nba_manager.manger(nba_props_data["NBA"], "NBA")

        nhl_manager.manger(nhl_mainline_data["NHL"], "NHL")
        nhl_manager.manger(nhl_props_data["NHL"], "NHL")

        ncaab_manager = ProcessManager(redis_database=12, difference_amount=1500, league="NCAAB")
        ncaab_manager.manger(ncaab_mainline_data["NCAAB"], "NCAAB")

        ufc_manager = ProcessManager(redis_database=13, difference_amount=1500, league="UFC")
        ufc_manager.manger(ufc_mainline_data["UFC"], "UFC")
        ufc_manager.manger(ufc_alternate_data["UFC"], "UFC")

    asyncio.run(main())

