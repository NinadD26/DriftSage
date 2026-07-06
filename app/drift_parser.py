from models import DriftChange


class DriftParser:

    @staticmethod
    def parse(plan_json):

        results = []

        for rc in plan_json.get(
            "resource_changes",
            []
        ):

            actions = rc["change"]["actions"]

            # Skip unchanged resources. A refresh-only plan
            # includes a "no-op" entry for every resource,
            # not just the ones that actually drifted.
            if actions == ["no-op"]:
                continue

            results.append(
                DriftChange(
                    resource=rc["address"],
                    action=actions,
                    before=rc["change"].get(
                        "before",
                        {}
                    ),
                    after=rc["change"].get(
                        "after",
                        {}
                    ),
                )
            )

        return results
