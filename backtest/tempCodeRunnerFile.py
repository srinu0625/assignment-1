ious_low2, "local_low2 :", local_low2)
                    print("   ")
                    time.sleep(1.5)

                    # Bullish entry
                    if local_high1 > 0:
                        if (current_high1 > local_high1) and  not bear and not flag:
                            loss_for_trade = abs(local_high1 - current_low1 + (tick_val * 4)) * contract_size
                            if loss_for_trade > risk:
                                num_of_lots = 1