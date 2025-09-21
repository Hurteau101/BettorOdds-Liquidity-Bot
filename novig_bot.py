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
    import asyncio

    async def main():
        with open("nfl_filters.json", "r") as f:
            nfl_filters = json.load(f)
        with open("ncaaf_filters.json", "r") as f:
            ncaaf_filters = json.load(f)

        sender_nfl = NovigSender(filter_data=nfl_filters, difference_amount=3000)
        sender_ncaaf = NovigSender(filter_data=ncaaf_filters, difference_amount=4000)

        nfl_data, ncaaf_data = await asyncio.gather(
            sender_nfl.runner(),
            sender_ncaaf.runner()
        )

        nfl_manager = ProcessManager(redis_database=1, difference_amount=1500, league="NFL")
        ncaaf_manager = ProcessManager(redis_database=2, difference_amount=1500, league="NCAAF")

        nfl_manager.manger(nfl_data["NFL"], "NFL")
        ncaaf_manager.manger(ncaaf_data["NCAAF"], "NCAAF")

    asyncio.run(main())