from dataclasses import dataclass
from datetime import datetime, timedelta
from copy import copy
from functools import partial
from typing import Any
from enums import GroupTypeEnum


@dataclass
class AgregateResultDTO:
    
    dataset: list[int]
    labels: list[str]


class AgregatePipilineBuilder:
   
    dt_from: datetime
    dt_upto: datetime
    group_type: GroupTypeEnum
    pipline: list[dict]

    def __init__(self, dt_from: datetime, dt_upto: datetime, group_type: GroupTypeEnum):
        self.dt_from = dt_from
        self.dt_upto = dt_upto
        self.group_type = group_type
        self.pipline = list()

    def _get_list_of_dates_by_delta(self, delta: timedelta) -> list[str]:
       
        start_date, end_date = copy(self.dt_from), self.dt_upto
        _list, time_format = [], self._get_time_format()
        while start_date <= end_date:
            _list.append(start_date.strftime(time_format))
            start_date += delta
        return _list

    def _get_list_of_month(self) -> list[str]:
       
        start_year, start_month = self.dt_from.year, self.dt_from.month
        end_year, end_month = self.dt_upto.year, self.dt_upto.month
        ym_start = 12 * start_year + start_month - 1
        ym_end = 12 * end_year + end_month
        _list, time_format = [], self._get_time_format()
        for ym in range(ym_start, ym_end):
            y, m = divmod(ym, 12)
            dt = datetime(year=y, month=m+1, day=1)
            _list.append(dt.strftime(time_format))
        return _list

    def get_time_value_map(self) -> dict[str, int]:
        _map = {
            GroupTypeEnum.hour: partial(self._get_list_of_dates_by_delta, timedelta(hours=1)),
            GroupTypeEnum.day: partial(self._get_list_of_dates_by_delta, timedelta(days=1)),
            GroupTypeEnum.month: self._get_list_of_month
        }
        _slice = _map.get(self.group_type)()
        return dict.fromkeys(_slice, 0)

    def _get_time_window(self) -> dict[str, datetime]:
   
        return {"$gte": self.dt_from, "$lte": self.dt_upto}

    def _get_time_format(self) -> str:
      
        _map = {
            GroupTypeEnum.hour: "%Y-%m-%dT%H:00:00",
            GroupTypeEnum.day: "%Y-%m-%dT00:00:00",
            GroupTypeEnum.month: "%Y-%m-01T00:00:00"
        }
        return _map.get(self.group_type)

    def _build_match(self, date_variable: str) -> None:
        
        self.pipline.append(
           {"$match": {date_variable: self._get_time_window()}}
        )

    def _build_group(self, date_variable: str, value_variable: str) -> None:
        
        self.pipline.append(
            {
                "$group": {
                    "_id": {
                        "label": {"$dateToString": {"format": self._get_time_format(), "date": f"${date_variable}"}}
                    },
                    "data": {"$sum": f"${value_variable}"}
                }
            }
        )

    def _build_sort(self, sort_value: int) -> None:
        
        self.pipline.append(
            {"$sort": {"_id": sort_value}}
        )

    def build_pipiline(self, date_variable: str, value_variable: str, sort_value: int) -> list[dict]:
        
        self._build_match(date_variable)
        self._build_group(date_variable, value_variable)
        self._build_sort(sort_value)
        return self.pipline


async def get_agregated(
    collection: Any,
    dt_from: datetime,
    dt_upto: datetime,
    group_type: GroupTypeEnum
) -> AgregateResultDTO:
    builder = AgregatePipilineBuilder(dt_from, dt_upto, group_type)
    pipeline = builder.build_pipiline(date_variable="dt", value_variable="value", sort_value=1)
    time_map = builder.get_time_value_map()

    async for document in collection.aggregate(pipeline):
        label, data = document["_id"]["label"], document["data"]
        time_map[label] = data

    return AgregateResultDTO(
        dataset=list(time_map.values()),
        labels=list(time_map.keys())
    )
