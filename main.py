from panther import Panther
from panther.app import GenericAPI
from panther.request import Request
from panther.response import TemplateResponse


def calculate_cost_split(items, orders, target_total_cost, total_discount):
    unit_prices = {item: total_cost / quantity for item, (quantity, total_cost) in items.items()}

    costs = {}
    for person, person_items in orders.items():
        cost = sum(quantity * unit_prices[item] for item, quantity in person_items.items())
        costs[person] = round(cost, 2)

    original_total = sum(costs.values())
    num_persons = len(orders)
    adjustment = (target_total_cost - original_total) / num_persons if num_persons > 0 else 0
    adjusted_costs = {person: round(cost + adjustment, 2) for person, cost in costs.items()}

    total_cost = sum(adjusted_costs.values())
    discounts = {person: round((cost / total_cost) * total_discount, 2) if total_cost > 0 else 0
                 for person, cost in adjusted_costs.items()}
    final_amounts = {person: round(cost - discounts[person], 2) for person, cost in adjusted_costs.items()}

    target_final_total = target_total_cost - total_discount
    rounded_amounts = {person: round(amount) for person, amount in final_amounts.items()}
    current_sum = sum(rounded_amounts.values())
    difference = current_sum - target_final_total

    if difference != 0:
        sorted_amounts = sorted(rounded_amounts.items(), key=lambda x: final_amounts[x[0]], reverse=True)
        adjusted_rounded = rounded_amounts.copy()
        i = 0
        while difference != 0 and i < len(sorted_amounts):
            person = sorted_amounts[i][0]
            if difference > 0:
                adjusted_rounded[person] -= 1
                difference -= 1
            elif difference < 0:
                adjusted_rounded[person] += 1
                difference += 1
            i = (i + 1) % len(sorted_amounts)
        rounded_amounts = adjusted_rounded

    return {
        "total_before_discount": total_cost,
        "total_after_discount": sum(rounded_amounts.values()),
        "final_amounts": rounded_amounts
    }


class IndexAPI(GenericAPI):
    def get(self):
        return TemplateResponse(name="index.html")

    def post(self, request: Request):
        try:
            items = eval(request.data["items"])
            orders = eval(request.data["orders"])
            target_total = float(request.data["target_total"])
            discount = float(request.data["discount"])

            context = calculate_cost_split(items, orders, target_total, discount)
        except Exception as e:
            context = {"error": str(e)}

        return TemplateResponse(name="index.html", context=context)


app = Panther(__name__, configs=__name__, urls={'': IndexAPI})
