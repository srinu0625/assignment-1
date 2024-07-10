
                num_of_lots = math.floor(risk / max_loss_for_trade )
                if num_of_lots >=max_num_lots:
                   num_of_lots = 5
            entry_price = local_high1 + (tick_val * 2)