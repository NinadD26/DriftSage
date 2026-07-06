from models import DriftChange


class DriftParser:

    @staticmethod
    def parse(plan_json):

        results = []

        # For a "-refresh-only" plan, actual drift (changes made
        # outside Terraform) is reported under "resource_drift",
        # NOT "resource_changes". "resource_changes" only holds
        # the plan's proposed actions, which are all "no-op" here
        # since a refresh-only plan never proposes real changes.
        for rc in plan_json.get(
            "resource_drift",
            []
        ):

            actions = rc["change"]["actions"]

            if actions == ["no-op"]:
                continue

            results.append(
                DriftChange(
                    resource=rc["address"],
                    action=actions,
                    before=rc["change"].get(
                        "before"
                    ) or {},
                    after=rc["change"].get(
                        "after"
                    ) or {},
                )
            )

        return results
    
    


# from models import DriftChange


# class DriftParser:

#     @staticmethod
#     def parse(plan_json):

#         results = []

#         for rc in plan_json.get(
#             "resource_changes",
#             []
#         ):

#             actions = rc["change"]["actions"]

#             # Skip unchanged resources. A refresh-only plan
#             # includes a "no-op" entry for every resource,
#             # not just the ones that actually drifted.
#             if actions == ["no-op"]:
#                 continue

#             results.append(
#                 DriftChange(
#                     resource=rc["address"],
#                     action=actions,
#                     before=rc["change"].get(
#                         "before",
#                         {}
#                     ),
#                     after=rc["change"].get(
#                         "after",
#                         {}
#                     ),
#                 )
#             )

#         return results
