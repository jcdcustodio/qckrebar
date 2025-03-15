from collections import defaultdict
import csv
import math
import os
import sys


clengths_metric = (6.0, 7.5, 9.0, 10.5, 12.0)
"""Standard rebar commercial lengths in meters: 6, 7.5, 9, 10.5, 12"""

clengths_english = (20, 25, 30, 35, 40)
"""Standard rebar commercial lengths in feet: 20, 25, 30, 35, 40"""

estimate_result = defaultdict(int)
excess_inventory = defaultdict(int)
cut_record = []


def main():
    if len(sys.argv) > 2:
        print("Usage: <file> | <file> -i/--input")
        sys.exit(1)
    elif len(sys.argv) == 2 and sys.argv[1] not in ("-i", "--input"):
        print("Usage: <file> | <file> -i/--input")
        sys.exit(1)
    elif len(sys.argv) == 1:
        is_import_mode = True
    else:
        is_import_mode = False

    wclengths = select_unit()
    cut_schedule = get_cut_schedule(is_import_mode)
    if not cut_schedule:
        print("Error: Cut schedule is empty")
        sys.exit(4)

    outputs = get_estimate(cut_schedule=cut_schedule.items(), wclengths=wclengths)

    print("Estimate Result")
    for length, quantity in sorted(outputs[0].items()):
        print(f"Length: {length}, Quantity: {quantity}")

    print("Unused Lengths")
    for length, quantity in sorted(outputs[1].items()):
        print(f"Length: {length}, Quantity: {quantity}")

    export_result(result=outputs)


def select_unit() -> list:
    """Helper function for main to select unit system: Metric (in m), English (in ft)."""

    while True:
        print("Select unit system: Metric (m), English (ft)")
        selected_unit = input("Enter (metric/english): ")

        if selected_unit.lower() not in ("metric", "english"):
            continue
        else:
            break

    match selected_unit:
        case "metric":
            return clengths_metric
        case "english":
            return clengths_english


def get_cut_schedule(import_mode: bool) -> dict:
    """Returns a processed version of cut schedule in dictionary format."""

    cut_schedule = defaultdict(float)

    if import_mode:
        filename = input("Import csv file: ")
        if not os.path.exists(filename):
            print("Error: File does not exist")
            sys.exit(1)
        elif not filename.lower().endswith(".csv"):
            print("Error: Imported file not a CSV")
            sys.exit(1)

        with open(filename, encoding="utf-8-sig") as cut_list:
            reader = csv.DictReader(
                cut_list, fieldnames=("cut_length", "quantity"), dialect="excel"
            )
            next(reader)
            for row in reader:
                try:
                    cut_schedule[float(row.get("cut_length"))] = float(
                        row.get("quantity")
                    )
                except ValueError:
                    print("Error: Invalid values detected")
                    sys.exit(1)
    else:
        print(
            "Enter cut schedule in this format: 'cut_length:quantity' or press CTRL+Z (CTRL+D) to stop"
        )
        while True:
            try:
                data_in = input("Enter 'cut_length:quantity': ")
                cut_length, quantity = data_in.split(":")
                cut_schedule[float(cut_length.strip())] = float(quantity.strip())
            except ValueError:
                print("Error: Invalid values detected")
                sys.exit(1)
            except EOFError:
                break

    return dict(cut_schedule)


def export_result(result: tuple):
    """Helper function to write results into a file. Returns three (3) files in a folder `results`."""

    # Create folder for results
    result_path = r"./results/"
    if not os.path.exists(result_path):
        os.makedirs(result_path)

    # Write estimate result into a new file
    with open(
        "results/rebar_estimates.csv", "w", encoding="utf-8-sig", newline=""
    ) as result_out:
        columns = ("rebar_length", "quantity")
        writer = csv.DictWriter(result_out, fieldnames=columns)
        writer.writeheader()
        for length, quantity in sorted(result[0].items()):
            writer.writerow({"rebar_length": length, "quantity": quantity})

    # Write unused excess list into a new file
    with open(
        "results/unused_excess.csv", "w", encoding="utf-8-sig", newline=""
    ) as result_out:
        columns = ("length", "quantity")
        writer = csv.DictWriter(result_out, fieldnames=columns)
        writer.writeheader()
        for length, quantity in sorted(result[1].items()):
            writer.writerow({"length": length, "quantity": quantity})

    # Write cut logs into a new file
    with open(
        "results/cut_log.csv", "w", encoding="utf-8-sig", newline=""
    ) as result_out:
        columns = [
            "produced_length",
            "produced_qty",
            "produced_type",
            "from_length",
            "from_length_type",
        ]
        writer = csv.DictWriter(result_out, fieldnames=columns)
        writer.writeheader()
        for row in result[2]:
            writer.writerow(row)


def get_optimal_clength(cut_length: float, clengths: list = clengths_metric) -> float:
    """Returns optimal commercial length based on produced waste/residue of cut length."""

    residues = [(round(clength % cut_length, 3), clength) for clength in clengths]
    return min(residues)[1]


def estimate_clength(
    cut_length: float,
    reqd_qty: int,
    wclength: float,
) -> int:
    """
    Returns the quantity of the chosen rebar commercial length
    based on the required quantity of cut length.

    Args:
        cut_length (float): Length of rebar to produce.
        reqd_qty (int): Quantity of **cut_length** to produce.
        wclength (float): Length of rebar to use. Must be from commercial length.

    Returns:
        reqd_qty_wclength (int): Quantity of **wclength** needed.

    """

    yield_qty = int(wclength // cut_length)
    reqd_qty_wclength = math.ceil(reqd_qty / yield_qty)
    record_cut(cut_length, reqd_qty, "cut length", wclength, "new rebar")

    yield_waste = round(wclength - cut_length * yield_qty, 3)
    yield_waste_qty = reqd_qty // yield_qty

    if yield_waste > 0 and yield_waste_qty > 0:
        excess_inventory[yield_waste] += yield_waste_qty
        record_cut(yield_waste, yield_waste_qty, "excess", wclength, "new rebar")

    if (reqd_qty / yield_qty) < reqd_qty_wclength:
        total_length = wclength * reqd_qty_wclength
        total_reqd = cut_length * reqd_qty
        waste_from_cut = yield_waste * yield_waste_qty

        waste_leftover = round(total_length - total_reqd - waste_from_cut, 3)
        excess_inventory[waste_leftover] += 1
        record_cut(waste_leftover, 1, "excess", wclength, "new rebar")

    return reqd_qty_wclength


def use_excess_length(
    cut_length: float,
    reqd_qty: int,
) -> int:
    """
    Utilize available excess lengths to produce cut lengths.
    Returns the adjusted required quantity of cut length to produce.

    """

    if not excess_inventory or reqd_qty == 0:
        return reqd_qty

    wqty = reqd_qty
    sorted_winventory = sorted(excess_inventory.items(), reverse=True)

    for excess_length, available_excess in sorted_winventory:
        if excess_length < cut_length:
            continue

        qty_per_excess = int(excess_length // cut_length)
        total_available_qty = qty_per_excess * available_excess

        # Case when chosen excess length is enough or not sufficient to produce required quantity
        # Used all available stock of chosen excess length
        if wqty >= total_available_qty:
            record_cut(
                cut_length,
                total_available_qty,
                "cut length",
                excess_length,
                "excess rebar",
            )
            excess_inventory.pop(excess_length, None)

            remain_excess = round(excess_length % cut_length, 3)
            if remain_excess > 0:
                excess_inventory[remain_excess] += available_excess
                record_cut(
                    remain_excess,
                    available_excess,
                    "excess",
                    excess_length,
                    "excess rebar",
                )

            wqty -= total_available_qty

        # Case when chosen excess length is more than sufficient to produce required quantity
        # Used portions of available stock of chosen excess length
        else:
            qty_used_full_excess = math.ceil(wqty / qty_per_excess)
            qty_leftover = wqty % qty_per_excess
            record_cut(cut_length, wqty, "cut length", excess_length, "excess rebar")

            excess_inventory[excess_length] -= qty_used_full_excess
            if excess_inventory[excess_length] <= 0:
                excess_inventory.pop(excess_length, None)

            # Remaining excess length from full cuts
            remain_excess = round(excess_length % cut_length, 3)
            if remain_excess > 0:
                excess_inventory[remain_excess] += qty_used_full_excess
                record_cut(
                    remain_excess,
                    qty_used_full_excess,
                    "excess",
                    excess_length,
                    "excess rebar",
                )

            # Remaining excess length from leftover
            if qty_leftover > 0:
                total_length_excess = excess_length * available_excess
                total_remain_excess = remain_excess * qty_used_full_excess
                total_length_reqd = cut_length * wqty

                leftover_excess = round(
                    total_length_excess - total_remain_excess - total_length_reqd, 3
                )
                excess_inventory[leftover_excess] += 1
                record_cut(leftover_excess, 1, "excess", excess_length, "excess rebar")

            wqty = 0

    return wqty


def record_cut(
    length_produced: float,
    qty_produced: int,
    type_produced: str,
    wlength: float,
    type_wlength: str,
):
    """
    Helper function to save record of produced cut and excess.

    Args:
        length_produced (float): Length of produced cut of rebar.
        qty_produced (int): Quantity of produced cut of rebar.
        type_produced (str): Type of produced cut of rebar (cut length/excess).
        wlength (float): Length used to produce cut_length.
        type_wlength (str): Type of length used to produce cut_length (from commercial length or excess).

    """

    record = {
        "produced_length": length_produced,
        "produced_qty": int(qty_produced),
        "produced_type": type_produced,
        "from_length": wlength,
        "from_length_type": type_wlength,
    }

    cut_record.append(record)


def get_estimate(cut_schedule: list, wclengths: list = clengths_metric) -> list:
    """Wrapper function for functions used to estimate rebars."""

    # Ensures cut_schedule contains valid values
    for cut_length, quantity in cut_schedule:
        if not isinstance(cut_length, (float, int)):
            raise ValueError("Invalid value found")
        if not isinstance(quantity, (float, int)):
            raise ValueError("Invalid input value found")

    # Ensures program runs at clean state
    estimate_result.clear()
    excess_inventory.clear()
    cut_record.clear()

    # Sort cut schedule starting at largest cut length
    input_cut_lengths = sorted(cut_schedule, reverse=True)

    # Estimate required quantity for each cut length
    for cut_length, quantity in input_cut_lengths:
        # Use excess lengths from previous cut if applicable
        wqty = use_excess_length(cut_length=cut_length, reqd_qty=quantity)
        if wqty <= 0:
            break

        # Pick optimal rebar length then use it for estimate
        clength = get_optimal_clength(cut_length=cut_length, clengths=wclengths)
        qty_clength = estimate_clength(
            cut_length=cut_length, reqd_qty=wqty, wclength=clength
        )

        # Record result
        estimate_result[clength] += qty_clength

    return estimate_result, excess_inventory, cut_record


if __name__ == "__main__":
    main()
