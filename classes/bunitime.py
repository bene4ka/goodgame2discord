from datetime import datetime, timezone, timedelta


class BuniTime:

    def is_it_time_to_buni(self, last_stream: datetime):
        current_time = datetime.now(timezone.utc)
        diff = current_time - last_stream
        diff_hours = diff.seconds/3600
        if diff_hours >= 3 and 9 <= current_time.hour <= 20:
            return True
        else:
            return False

