============================================================================================================================ short test summary info =============================================================================================================================
FAILED tests/integration/test_blink_integration.py::TestBlinkIntegration::test_complete_unblink_workflow - AssertionError: assert '<S0012345011F06D00FG>' == '<S0012345011F06D00FK>'
  
  - <S0012345011F06D00FK>
  ?                    ^
  + <S0012345011F06D00FG>
  ?                    ^
FAILED tests/integration/test_blink_integration.py::TestBlinkIntegration::test_end_to_end_workflow_with_replies - AssertionError: assert '<S0012345011F06D00FG>' == '<S0012345011F06D00FK>'
  
  - <S0012345011F06D00FK>
  ?                    ^
  + <S0012345011F06D00FG>
  ?                    ^
FAILED tests/integration/test_discovery_integration.py::TestDiscoverIntegration::test_checksum_validation_integration - AssertionError: assert False is True
 +  where False = ReplyTelegram(checksum='FM', raw_telegram='<R0012345011F01DFM>', checksum_validated=False, timestamp=datetime.datetime(2025, 9, 22, 0, 47, 13, 718291), serial_number='0012345011', system_function=<SystemFunction.DISCOVERY: '01'>, data='00', datapoint_type=<DataPointType.MODULE_TYPE: '00'>, data_value='D').checksum_validated
FAILED tests/integration/test_link_number_integration.py::TestLinkNumberIntegration::test_complete_set_link_number_workflow - AssertionError: assert '<S0012345005F04D0425FC>' == '<S0012345005F04D0425FO>'
  
  - <S0012345005F04D0425FO>
  ?                      ^
  + <S0012345005F04D0425FC>
  ?                      ^
FAILED tests/integration/test_link_number_integration.py::TestLinkNumberIntegration::test_end_to_end_workflow_with_replies - AssertionError: assert '<S0012345005F04D0425FC>' == '<S0012345005F04D0425FO>'
  
  - <S0012345005F04D0425FO>
  ?                      ^
  + <S0012345005F04D0425FC>
  ?                      ^
FAILED tests/unit/test_encoding/test_latin1_edge_cases.py::TestLatin1EdgeCases::test_raw_hex_data_decoding - AssertionError: assert '<R0020044966F02D18+31,5§CIE' == '<R0012345006F02D18+31,5§CIE'
  
  - <R0012345006F02D18+31,5§CIE
  ?     - ---
  + <R0020044966F02D18+31,5§CIE
  ?        ++++
FAILED tests/unit/test_encoding/test_latin1_edge_cases.py::TestLatin1EdgeCases::test_utf8_vs_latin1_comparison - AssertionError: assert '<R0020044966F02D18+31,5§CIE' == '<R0012345006F02D18+31,5§CIE'
  
  - <R0012345006F02D18+31,5§CIE
  ?     - ---
  + <R0020044966F02D18+31,5§CIE
  ?        ++++
FAILED tests/unit/test_services/test_blink_service.py::TestBlinkService::test_generate_blink_telegram_valid - AssertionError: assert '<S0012345011F05D00FF>' == '<S0012345011F05D00FJ>'
  
  - <S0012345011F05D00FJ>
  ?                    ^
  + <S0012345011F05D00FF>
  ?                    ^
FAILED tests/unit/test_services/test_blink_service.py::TestBlinkService::test_generate_unblink_telegram_valid - AssertionError: assert '<S0012345011F06D00FG>' == '<S0012345011F06D00FK>'
  
  - <S0012345011F06D00FK>
  ?                    ^
  + <S0012345011F06D00FG>
  ?                    ^
FAILED tests/unit/test_services/test_blink_service.py::TestBlinkService::test_create_unblink_telegram_object - AssertionError: assert '<S0012345011F06D00FG>' == '<S0012345011F06D00FK>'
  
  - <S0012345011F06D00FK>
  ?                    ^
  + <S0012345011F06D00FG>
  ?                    ^
FAILED tests/unit/test_services/test_discovery_service.py::TestDiscoverService::test_generate_discover_summary - KeyError: '0020'
FAILED tests/unit/test_services/test_discovery_service.py::TestDiscoverService::test_format_discover_results_with_devices - AssertionError: assert '0020xxxx: 3 device(s)' in '=== Device Discover Results ===\nTotal Responses: 3\nUnique Devices: 3\nValid Checksums: 2/3 (66.7%)\n\nDiscovered Devices:\n----------------------------------------\n\u2713 0012345011\n\u2717 0012345006\n\u2713 0012345003\n\nSerial Number Distribution:\n  0012xxxx: 3 device(s)'
FAILED tests/unit/test_services/test_link_number_service.py::TestLinkNumberService::test_generate_set_link_number_telegram_valid - AssertionError: assert '<S0012345005F04D0425FC>' == '<S0012345005F04D0425FO>'
  
  - <S0012345005F04D0425FO>
  ?                      ^
  + <S0012345005F04D0425FC>
  ?                      ^
FAILED tests/unit/test_services/test_link_number_service.py::TestLinkNumberService::test_create_set_link_number_telegram_object - AssertionError: assert '<S0012345005F04D0425FC>' == '<S0012345005F04D0425FO>'
  
  - <S0012345005F04D0425FO>
  ?                      ^
  + <S0012345005F04D0425FC>
  ?                      ^
FAILED tests/unit/test_services/test_xp20_server_service.py::TestXP20ServerService::test_generate_discover_response - AssertionError: assert '<R0012345002F01DFC>' == '<R0012345002F01DFM>'
  
  - <R0012345002F01DFM>
  ?                  ^
  + <R0012345002F01DFC>
  ?                  ^
FAILED tests/unit/test_services/test_xp20_server_service.py::TestXP20ServerService::test_generate_module_type_response - AssertionError: assert '<R0012345002F02D0733FG>' == '<R0012345002F02D0733FI>'
  
  - <R0012345002F02D0733FI>
  ?                      ^
  + <R0012345002F02D0733FG>
  ?                      ^
FAILED tests/unit/test_services/test_xp20_server_service.py::TestXP20ServerService::test_process_system_telegram_module_type - AssertionError: assert '<R0012345002F02D0733FG>' == '<R0012345002F02D0733FI>'
  
  - <R0012345002F02D0733FI>
  ?                      ^
  + <R0012345002F02D0733FG>
  ?                      ^
FAILED tests/unit/test_services/test_xp20_server_service.py::TestXP20ServerService::test_process_system_telegram_broadcast - AssertionError: assert '<R0012345002F02D0733FG>' == '<R0012345002F02D0733FI>'
  
  - <R0012345002F02D0733FI>
  ?                      ^
  + <R0012345002F02D0733FG>
  ?                      ^
FAILED tests/unit/test_services/test_xp230_server_service.py::TestXP230ServerService::test_generate_module_type_response - AssertionError: assert '<R0012345011F02D0734FD>' == '<R0012345011F02D0734FP>'
  
  - <R0012345011F02D0734FP>
  ?                      ^
  + <R0012345011F02D0734FD>
  ?                      ^
FAILED tests/unit/test_services/test_xp230_server_service.py::TestXP230ServerService::test_process_system_telegram_module_type - AssertionError: assert '<R0012345011F02D0734FD>' == '<R0012345011F02D0734FP>'
  
  - <R0012345011F02D0734FP>
  ?                      ^
  + <R0012345011F02D0734FD>
  ?                      ^
FAILED tests/unit/test_services/test_xp24_server_service.py::TestXP24ServerService::test_generate_discover_response - AssertionError: assert '<R0012345004F01DFE>' == '<R0012345004F01DFC>'
  
  - <R0012345004F01DFC>
  ?                  ^
  + <R0012345004F01DFE>
  ?                  ^
FAILED tests/unit/test_services/test_xp24_server_service.py::TestXP24ServerService::test_generate_module_type_response - AssertionError: assert '<R0012345004F02D077GH>' == '<R0012345004F02D077GB>'
  
  - <R0012345004F02D077GB>
  ?                     ^
  + <R0012345004F02D077GH>
  ?                     ^
FAILED tests/unit/test_services/test_xp24_server_service.py::TestXP24ServerService::test_process_system_telegram_module_type - AssertionError: assert '<R0012345004F02D077GH>' == '<R0012345004F02D077GB>'
  
  - <R0012345004F02D077GB>
  ?                     ^
  + <R0012345004F02D077GH>
  ?                     ^
FAILED tests/unit/test_services/test_xp24_server_service.py::TestXP24ServerService::test_process_system_telegram_broadcast - AssertionError: assert '<R0012345004F02D077GH>' == '<R0012345004F02D077GB>'
  
  - <R0012345004F02D077GB>
  ?                     ^
  + <R0012345004F02D077GH>
  ?                     ^
FAILED tests/unit/test_services/test_xp33_server_service.py::TestXP33ServerService::test_generate_discover_response - AssertionError: assert '<R0012345003F01DFD>' == '<R0012345003F01DFN>'
  
  - <R0012345003F01DFN>
  ?                  ^
  + <R0012345003F01DFD>
  ?                  ^
FAILED tests/unit/test_services/test_xp33_server_service.py::TestXP33ServerService::test_generate_version_response - AssertionError: assert '<R0012345003F02D02XP33LR_V0.00.00HN>' == '<R0012345003F02D02XP33LR_V0.00.00HD>'
  
  - <R0012345003F02D02XP33LR_V0.00.00HD>
  ?                                   ^
  + <R0012345003F02D02XP33LR_V0.00.00HN>
  ?                                   ^
FAILED tests/unit/test_services/test_xp33_server_service.py::TestXP33ServerService::test_generate_module_type_response - AssertionError: assert '<R0012345003F02D0730FE>' == '<R0012345003F02D0730FK>'
  
  - <R0012345003F02D0730FK>
  ?                      ^
  + <R0012345003F02D0730FE>
  ?                      ^
FAILED tests/unit/test_services/test_xp33_server_service.py::TestXP33ServerService::test_generate_status_response - AssertionError: assert '<R0012345003F02D1000FB>' == '<R0012345003F02D1000FP>'
  
  - <R0012345003F02D1000FP>
  ?                      ^
  + <R0012345003F02D1000FB>
  ?                      ^
FAILED tests/unit/test_services/test_xp33_server_service.py::TestXP33ServerService::test_generate_channel_states_response - AssertionError: assert '<R0012345003F02D12000000000GD>' == '<R0012345003F02D10012345012GN>'
  
  - <R0012345003F02D10012345012GN>
  + <R0012345003F02D12000000000GD>
FAILED tests/unit/test_services/test_xp33_server_service.py::TestXP33ServerService::test_generate_link_number_response - AssertionError: assert '<R0012345003F02D0404FA>' == '<R0012345003F02D0404FO>'
  
  - <R0012345003F02D0404FO>
  ?                      ^
  + <R0012345003F02D0404FA>
  ?                      ^
FAILED tests/unit/test_services/test_xp33_server_service.py::TestXP33ServerService::test_generate_link_number_response_legacy_alias - AssertionError: assert '<R0012345003F02D0404FA>' == '<R0012345003F02D0404FO>'
  
  - <R0012345003F02D0404FO>
  ?                      ^
  + <R0012345003F02D0404FA>
  ?                      ^
FAILED tests/unit/test_services/test_xp33_server_service.py::TestXP33ServerService::test_process_system_telegram_discover - AssertionError: assert '<R0012345003F01DFD>' == '<R0012345003F01DFN>'
  
  - <R0012345003F01DFN>
  ?                  ^
  + <R0012345003F01DFD>
  ?                  ^
FAILED tests/unit/test_services/test_xp33_server_service.py::TestXP33ServerService::test_process_system_telegram_version_request - AssertionError: assert '<R0012345003F02D02XP33LR_V0.00.00HN>' == '<R0012345003F02D02XP33LR_V0.00.00HD>'
  
  - <R0012345003F02D02XP33LR_V0.00.00HD>
  ?                                   ^
  + <R0012345003F02D02XP33LR_V0.00.00HN>
  ?                                   ^
FAILED tests/unit/test_services/test_xp33_server_service.py::TestXP33ServerService::test_channel_states_with_different_levels - AssertionError: assert '<R0012345003F02D12324B19000BM>' == '<R0012345003F02D12324B19000BC>'
  
  - <R0012345003F02D12324B19000BC>
  ?                             ^
  + <R0012345003F02D12324B19000BM>
  ?                             ^
FAILED tests/unit/test_services/test_xp33_server_service.py::TestXP33ServerService::test_integration_with_telegram_service - AssertionError: assert '<R0012345003F02D02XP33LR_V0.00.00HN>' == '<R0012345003F02D02XP33LR_V0.00.00HD>'
  
  - <R0012345003F02D02XP33LR_V0.00.00HD>
  ?                                   ^
  + <R0012345003F02D02XP33LR_V0.00.00HN>
  ?                                   ^
========================================================================================================================= 35 failed, 677 passed in 3.55s =