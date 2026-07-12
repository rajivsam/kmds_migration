1. Use the dd-parser-cleaner package's notebook utils to get the clean dataset
2. Use the featurization package's get_package_info() to get the interfaces exposed by the package.
3. Use the following information filter the data from the dataset in step 1, drop tickets with assingnment_group column value set to '?'
4. Using the dataset from the previous step, find the last closed ticket in the dataset. This is the last ticket number that is closed. Mark that time stamp as end of observation period. Go one year from that time, that is the start of the observation period. Tickets opened and closed between the start and end of the observation period are the candidates for the study.
5. Filter the dataset above on the tickets that are closed. Group the resulting dataset by assignment group and count the unique ticket numbers in each group. Define a threshold called MIN_TICKET_CLOSURE set to 20. Store the resulting group numbers in a support_level_clear_list.
6. Filter the dataset from step 4 to include only the ticket numbers from the above list
7. Using the survival featurization pipeline in the featurization package, develop a survival pipeline for the dataset.
8. Using the notebook_utils of the featurization package, not the dd-parser-cleaner, write the prepared survival dataset to the featurization complete dataset location. There should be a configuration for this in the featurization_config.yaml
