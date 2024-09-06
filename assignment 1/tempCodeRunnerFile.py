try:
                    # Extracting current and previous values for high and low from data1
                    current_time1 = row1[time_column_name]
                    high1 = float(row1[high_column_name])
                    low1 = float(row1[low_column_name])
                    if (high1 > current_high1) or (low1 < current_low1):
                        previous_high1 = current_high1
                        previous_low1 = current_low1
                        current_high1 = high1
                        current_low1 = low1

                    # Extracting current and previous values for high and low from data2
                    current_time2 = (data2.at[index2 - 1, time_column_name])
                    high2 = float(row2[high_column_name])
                    low2 = float(row2[low_column_name])
                    if (high2 > current_high2) or (low2 < current_low2):
                        previous_high2 = current_high2
                        previous_low2 = current_low2
                        current_high2 = high2
                        current_low2 = low2

                    # case 1 for data1
                    if current_high1 > previous_high1:
                        temp_high1 = current_high1
                        local_low1 = temp_low1

                    if current_low1 < previous_low1:
                        temp_low1 = current_low1
                        local_high1 = temp_high1

                    if current_high1 > previous_high1 and current_low1 < previous_low1 :
                        local_high1 = temp_high1
                        local_low1 = temp_low1
                        
                    # Printing data for data2
                    print("----DAILY :----", current_time1)
                    print("Current High1 :", current_high1, "Previous High1 :", previous_high1, "local_high1 :", local_high1)
                    print("Current Low1 :", current_low1, "Previous Low1 :", previous_low1, "local_low1 :", local_low1)
                    print("   ")
                    time.sleep(1.5)

                    # case 1 for data2
                    if current_high2 > previous_high2:
                        temp_high2 = current_high2
                        local_low2 = temp_low2

                    if current_low2 < previous_low2:
                        temp_low2 = current_low2
                        local_high2 = temp_high2

                    if current_high2 > previous_high2 and current_low2 < previous_low2 :
                        local_high2 = temp_high2
                        local_low2 = temp_low2

                    # Printing data for data2
                    print("----WEEKLY :----", current_time2)
                    print("Current High2 :", current_high2, "Previous High2 :", previous_high2, "local_high2 :", local_high2)
                    print("Current Low2 :", current_low2, "Previous Low2 :", previous_low2, "local_low2 :", local_low2)
                    print("   ")
                    time.sleep(1.5)

                    # Bullish entry
                    if local_high1 > 0:
                        if (current_high1 > local_high1) and (local_low1 >= local_low2) and not bear and not flag:
                            loss_for_trade = abs(local_high1 - current_low1 + (tick_val * 4)) * contract_size
                            if loss_for_trade > risk:
                                num_of_lots = 1
                                continue
                            else:
                                num_of_lots = math.floor(risk / loss_for_trade)
                                if num_of_lots >= max_num_lots:
                                    num_of_lots = 5
                                entry_price = local_high1 + (tick_val * 2)
                                exit_price = current_low1 - (tick_val * 2)
                                print("\033[32m<------ LONG ENTRY ------>(CH1 > LH1) AND (LL1 >= LL2)\033[0m")
                                print("       ENTRY PRICE  = ", entry_price)
                                print("        num_of_lots = ", round(num_of_lots))
                                print("     loss_for_trade = ", round(loss_for_trade))
                                print("----------------------------------------------------------")
                                bull = True
                                flag = True
                                continue
                    
                    # updating exit price
                    if bull and current_low1 > exit_price:
                        exit_price = current_low1 

                    # Bullish Exit
                    if current_low1 < exit_price and bull and flag:
                        num_of_trades += 1
                        bull = False
                        flag = False

                        # Calculate P&L
                        pnl = (exit_price - entry_price) * num_of_lots * contract_size
                        TOTAL_P_L += pnl
                        total_long_pnl += pnl
                        integer_pnl = float(pnl)  # Extract the integer part of the P&L

                        # declaring maxloss and maxprofit
                        max_profit = max(max_profit, pnl)
                        max_loss = min(max_loss, pnl)

                        # Check if integer part of P&L is positive or negative and set color accordingly
                        if integer_pnl >= 0:
                            pnl_color = "\033[32m"  # Green color
                        else:
                            pnl_color = "\033[31m"  # Red color

                        # Add to total positive or negative P&L based on the result
                        if pnl >= 0:
                            positive_pnl += pnl
                            total_positive_trades +=1
                        else:
                            negative_pnl += pnl
                            total_negative_trades +=1

                        print("\033[32m<------ LONG EXIT ------>(LL1 >\033[0m")
                        print("         EXIT PRICE = ", exit_price)
                        print("        num_of_lots = ", round(num_of_lots))
                        print("      num_of_trades = ", num_of_trades)
                        print("         max_profit = ", round(max_profit, 2))
                        print("           max_loss = ", round(max_loss, 2))
                        print("       P&L_Of_trade = ", pnl_color, round(integer_pnl, 2), "\033[0m")
                        print("---------------------------------------------------------")
                        continue

                    # Bearish entry----------------------------------------------------------------------------
                    if local_low1 > 0:
                        if (current_low1 < local_low1) and (local_high1 <= local_high2) and not bull and not flag:
                            loss_for_trade = abs(current_high1 - local_low1 + ( tick_val * 4)) * contract_size
                            if loss_for_trade > risk:
                                num_of_lots = 1
                                continue
                            else:
                                num_of_lots = math.floor(risk / loss_for_trade)
                                if num_of_lots >= max_num_lots:
                                    num_of_lots = 5
                                entry_price = local_low1 - (tick_val * 2)
                                exit_price = current_high1 + (tick_val * 2)
                                print("\033[31m<------ SHORT ENTRY ------> (CL1 < LL1) AND (LH1 <= LH2)\033[0m")
                                print("        ENTRY PRICE = ", entry_price)
                                print("        num_of_lots = ", round(num_of_lots))
                                print("     loss_for_trade = ", round(loss_for_trade))
                                print("------------------------------------------------")
                                bear = True
                                flag = True
                                continue

                    if bear and current_high1 < exit_price:
                        exit_price = current_high1

                    # Bearish exit
                    if current_high1 > exit_price and bear and flag:
                        number_of_positions -= 1
                        num_of_trades += 1
                        bear = False
                        flag = False

                        # Calculate P&L
                        pnl = (entry_price - exit_price) * num_of_lots * contract_size
                        TOTAL_P_L += pnl
                        total_short_pnl += pnl
                        integer_pnl = float(pnl)  # Extract the integer part of the P&L

                        # declaring maxloss and maxprofit
                        max_profit = max(max_profit, pnl)
                        max_loss = min(max_loss, pnl)

                        # Check if integer part of P&L is positive or negative and set color accordingly
                        if integer_pnl >= 0:
                            pnl_color = "\033[32m"  # Green color
                        else:
                            pnl_color = "\033[31m"  # Red color

                        # Add to total positive or negative P&L based on the result
                        if pnl >= 0:
                            positive_pnl += pnl
                            total_positive_trades +=1
                        else:
                            negative_pnl += pnl
                            total_negative_trades +=1

                        print("\033[31m<------ SHORT EXIT ------>(LH1 >)\033[0m")
                        print("         EXIT PRICE = ", exit_price)
                        print("        num_of_lots = ", round(num_of_lots))
                        print("      num_of_trades = ", num_of_trades)
                        print("         max_profit = ", round(max_profit, 2))
                        print("           max_loss = ", round(max_loss, 2))
                        print("       P&L_of_trade = ", pnl_color, round(integer_pnl),"\033[0m")
                        print("------------------------------------------------")
                        continue

                except Exception as e:
                    print("Error:", e)

                finally:
                    print("------------------------------------------End of iteration---------------------------------------------")