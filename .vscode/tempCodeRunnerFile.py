 # case 1 for data1-----------------------------------------------------------------------------------
        if(current_high1 > previous_high1):
            temp_high1 = current_high1
            

        if(current_low1 < previous_low1):
            temp_low1 = current_low1
        # case 2 for data1-----------------------------------------------------------------------------------
        if(current_high1 > previous_high1):
            local_low1 = temp_low1
            if(temp_low1 != local_low1): 
               prev_local_low1 = local_low1
            

        if(current_low1 < previous_low1):
            local_high1 = temp_high1
            if(temp_high1 != local_high1):
                prev_local_high1 = local_high1
         
        

        # Printing data for data1

        print("---60 MIN---:", current_time1)
        print("Current High1 :", current_high1, "Previous High1 :", previous_high1, "local_high1 :", local_high1,"prev_local_high1 :",prev_local_high1)
        print("Current Low1 :", current_low1, "Previous Low1 :", previous_low1, "local_low1 :", local_low1,"prev_local_low1 :",prev_local_low1)
        print("   ")
        time.sleep(0.5)

    # case 1 for data2-----------------------------------------------------------------------------------
        if (current_high2 > previous_high2):
            temp_high2 = current_high2

        if (current_low2 < previous_low2):
            temp_low2 = current_low2
        # case 2 for data1-----------------------------------------------------------------------------------
        if(current_high2 > previous_high2):
            local_low2 = temp_low2
            if(temp_low2 != local_low2): 
               prev_local_low2 = local_low2
            

        if(current_low2 < previous_low2):
            local_high2 = temp_high2
            if(temp_high2 != local_high2):
                prev_local_high2 = local_high2
        
        # Printing data for data2

        print("---240 MIN---:", current_time2)
        print("Current High2 :", current_high2, "Previous High2 :", previous_high2, "local_high2 :", local_high2,"prev_local_high2 :",prev_local_high2)
        print("Current Low2 :", current_low2, "Previous Low2 :", previous_low2, "local_low2 :", local_low2,"prev_local_low2 :",prev_local_low2)
        print("   ")
        time.sleep(0.5)

        # case 1 for data3-----------------------------------------------------------------------------------
        if (current_high3 > previous_high3):
            temp_high3 = current_high3

        if (current_low3 < previous_low3):
            temp_low3 = current_low3
        # case 2 for data1-----------------------------------------------------------------------------------
        # case 2 for data1-----------------------------------------------------------------------------------
        if(current_high3 > previous_high3):
            local_low3 = temp_low3
            if(temp_low3 != local_low3): 
               prev_local_low3 = local_low3
            

        if(current_low3 < previous_low3):
            local_high3 = temp_high3
            if(temp_high3 != local_high3):
                prev_local_high3 = local_high3

        # Printing data for data3

        print("----DAILY----:", current_time3)
        print("Current High3 :", current_high3, "Previous High3 :", previous_high3, "local_high3 :", local_high3,"prev_local_high3 :",prev_local_high3)
        print("Current Low3 :", current_low3, "Previous Low3 :", previous_low3, "local_low3 :", local_low3,"prev_local_low3 :",prev_local_low3)
        time.sleep(0.5)
        print("   ")
