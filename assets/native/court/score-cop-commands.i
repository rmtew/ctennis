        ; CT12 status: full row at native y0, restore all planes.
        dc.w $2c01,$fffe
score_cop_224_hi: dc.w $00e0,0
score_cop_224_lo: dc.w $00e2,0
score_cop_225_hi: dc.w $00e4,0
score_cop_225_lo: dc.w $00e6,0
score_cop_226_hi: dc.w $00e8,0
score_cop_226_lo: dc.w $00ea,0
score_cop_227_hi: dc.w $00ec,0
score_cop_227_lo: dc.w $00ee,0
        dc.w $3401,$fffe
score_cop_228_hi: dc.w $00e0,0
score_cop_228_lo: dc.w $00e2,0
score_cop_229_hi: dc.w $00e4,0
score_cop_229_lo: dc.w $00e6,0
score_cop_230_hi: dc.w $00e8,0
score_cop_230_lo: dc.w $00ea,0
score_cop_231_hi: dc.w $00ec,0
score_cop_231_lo: dc.w $00ee,0
        ; CT12 mode: full row at native y32, restore all planes.
        dc.w $4c01,$fffe
score_cop_232_hi: dc.w $00e0,0
score_cop_232_lo: dc.w $00e2,0
score_cop_233_hi: dc.w $00e4,0
score_cop_233_lo: dc.w $00e6,0
score_cop_234_hi: dc.w $00e8,0
score_cop_234_lo: dc.w $00ea,0
score_cop_235_hi: dc.w $00ec,0
score_cop_235_lo: dc.w $00ee,0
        dc.w $5401,$fffe
score_cop_237_hi: dc.w $00e4,0
score_cop_237_lo: dc.w $00e6,0
score_cop_238_hi: dc.w $00e8,0
score_cop_238_lo: dc.w $00ea,0
        ; Red logical B point glyphs: high planes for native rows40..55.
        dc.w $5401,$fffe
score_cop_240_hi: dc.w $00e0,0
score_cop_240_lo: dc.w $00e2,0
score_cop_241_hi: dc.w $00ec,0
score_cop_241_lo: dc.w $00ee,0
        ifd ENHANCED_INTERFACE
        dc.w $544d,$fffe
        else
        dc.w $543d,$fffe
        endif
score_cop_0_hi: dc.w $00e8,0
score_cop_0_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $54a9,$fffe
        else
        dc.w $5499,$fffe
        endif
score_cop_1_hi: dc.w $00e8,0
score_cop_1_lo: dc.w $00ea,0
        dc.w $54d1,$fffe
score_cop_2_hi: dc.w $00e8,0
score_cop_2_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $554d,$fffe
        else
        dc.w $553d,$fffe
        endif
score_cop_3_hi: dc.w $00e8,0
score_cop_3_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $55a9,$fffe
        else
        dc.w $5599,$fffe
        endif
score_cop_4_hi: dc.w $00e8,0
score_cop_4_lo: dc.w $00ea,0
        dc.w $55d1,$fffe
score_cop_5_hi: dc.w $00e8,0
score_cop_5_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $564d,$fffe
        else
        dc.w $563d,$fffe
        endif
score_cop_6_hi: dc.w $00e8,0
score_cop_6_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $56a9,$fffe
        else
        dc.w $5699,$fffe
        endif
score_cop_7_hi: dc.w $00e8,0
score_cop_7_lo: dc.w $00ea,0
        dc.w $56d1,$fffe
score_cop_8_hi: dc.w $00e8,0
score_cop_8_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $574d,$fffe
        else
        dc.w $573d,$fffe
        endif
score_cop_9_hi: dc.w $00e8,0
score_cop_9_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $57a9,$fffe
        else
        dc.w $5799,$fffe
        endif
score_cop_10_hi: dc.w $00e8,0
score_cop_10_lo: dc.w $00ea,0
        dc.w $57d1,$fffe
score_cop_11_hi: dc.w $00e8,0
score_cop_11_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $584d,$fffe
        else
        dc.w $583d,$fffe
        endif
score_cop_12_hi: dc.w $00e8,0
score_cop_12_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $58a9,$fffe
        else
        dc.w $5899,$fffe
        endif
score_cop_13_hi: dc.w $00e8,0
score_cop_13_lo: dc.w $00ea,0
        dc.w $58d1,$fffe
score_cop_14_hi: dc.w $00e8,0
score_cop_14_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $594d,$fffe
        else
        dc.w $593d,$fffe
        endif
score_cop_15_hi: dc.w $00e8,0
score_cop_15_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $59a9,$fffe
        else
        dc.w $5999,$fffe
        endif
score_cop_16_hi: dc.w $00e8,0
score_cop_16_lo: dc.w $00ea,0
        dc.w $59d1,$fffe
score_cop_17_hi: dc.w $00e8,0
score_cop_17_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5a4d,$fffe
        else
        dc.w $5a3d,$fffe
        endif
score_cop_18_hi: dc.w $00e8,0
score_cop_18_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5aa9,$fffe
        else
        dc.w $5a99,$fffe
        endif
score_cop_19_hi: dc.w $00e8,0
score_cop_19_lo: dc.w $00ea,0
        dc.w $5ad1,$fffe
score_cop_20_hi: dc.w $00e8,0
score_cop_20_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5b4d,$fffe
        else
        dc.w $5b3d,$fffe
        endif
score_cop_21_hi: dc.w $00e8,0
score_cop_21_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5ba9,$fffe
        else
        dc.w $5b99,$fffe
        endif
score_cop_22_hi: dc.w $00e8,0
score_cop_22_lo: dc.w $00ea,0
        dc.w $5bd1,$fffe
score_cop_23_hi: dc.w $00e8,0
score_cop_23_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5c4d,$fffe
        else
        dc.w $5c3d,$fffe
        endif
score_cop_24_hi: dc.w $00e8,0
score_cop_24_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5ca9,$fffe
        else
        dc.w $5c99,$fffe
        endif
score_cop_25_hi: dc.w $00e8,0
score_cop_25_lo: dc.w $00ea,0
        dc.w $5cd1,$fffe
score_cop_26_hi: dc.w $00e8,0
score_cop_26_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5d4d,$fffe
        else
        dc.w $5d3d,$fffe
        endif
score_cop_27_hi: dc.w $00e8,0
score_cop_27_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5da9,$fffe
        else
        dc.w $5d99,$fffe
        endif
score_cop_28_hi: dc.w $00e8,0
score_cop_28_lo: dc.w $00ea,0
        dc.w $5dd1,$fffe
score_cop_29_hi: dc.w $00e8,0
score_cop_29_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5e4d,$fffe
        else
        dc.w $5e3d,$fffe
        endif
score_cop_30_hi: dc.w $00e8,0
score_cop_30_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5ea9,$fffe
        else
        dc.w $5e99,$fffe
        endif
score_cop_31_hi: dc.w $00e8,0
score_cop_31_lo: dc.w $00ea,0
        dc.w $5ed1,$fffe
score_cop_32_hi: dc.w $00e8,0
score_cop_32_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5f4d,$fffe
        else
        dc.w $5f3d,$fffe
        endif
score_cop_33_hi: dc.w $00e8,0
score_cop_33_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $5fa9,$fffe
        else
        dc.w $5f99,$fffe
        endif
score_cop_34_hi: dc.w $00e8,0
score_cop_34_lo: dc.w $00ea,0
        dc.w $5fd1,$fffe
score_cop_35_hi: dc.w $00e8,0
score_cop_35_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $604d,$fffe
        else
        dc.w $603d,$fffe
        endif
score_cop_36_hi: dc.w $00e8,0
score_cop_36_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $60a9,$fffe
        else
        dc.w $6099,$fffe
        endif
score_cop_37_hi: dc.w $00e8,0
score_cop_37_lo: dc.w $00ea,0
        dc.w $60d1,$fffe
score_cop_38_hi: dc.w $00e8,0
score_cop_38_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $614d,$fffe
        else
        dc.w $613d,$fffe
        endif
score_cop_39_hi: dc.w $00e8,0
score_cop_39_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $61a9,$fffe
        else
        dc.w $6199,$fffe
        endif
score_cop_40_hi: dc.w $00e8,0
score_cop_40_lo: dc.w $00ea,0
        dc.w $61d1,$fffe
score_cop_41_hi: dc.w $00e8,0
score_cop_41_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $624d,$fffe
        else
        dc.w $623d,$fffe
        endif
score_cop_42_hi: dc.w $00e8,0
score_cop_42_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $62a9,$fffe
        else
        dc.w $6299,$fffe
        endif
score_cop_43_hi: dc.w $00e8,0
score_cop_43_lo: dc.w $00ea,0
        dc.w $62d1,$fffe
score_cop_44_hi: dc.w $00e8,0
score_cop_44_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $634d,$fffe
        else
        dc.w $633d,$fffe
        endif
score_cop_45_hi: dc.w $00e8,0
score_cop_45_lo: dc.w $00ea,0
        ifd ENHANCED_INTERFACE
        dc.w $63a9,$fffe
        else
        dc.w $6399,$fffe
        endif
score_cop_46_hi: dc.w $00e8,0
score_cop_46_lo: dc.w $00ea,0
        dc.w $63d1,$fffe
score_cop_47_hi: dc.w $00e8,0
score_cop_47_lo: dc.w $00ea,0
        dc.w $6401,$fffe
score_cop_242_hi: dc.w $00e0,0
score_cop_242_lo: dc.w $00e2,0
score_cop_243_hi: dc.w $00ec,0
score_cop_243_lo: dc.w $00ee,0
        ifd ENHANCED_INTERFACE
        dc.w $744b,$fffe
        else
        dc.w $743b,$fffe
        endif
score_cop_48_hi: dc.w $00e4,0
score_cop_48_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $74ab,$fffe
        else
        dc.w $749b,$fffe
        endif
score_cop_49_hi: dc.w $00e4,0
score_cop_49_lo: dc.w $00e6,0
        dc.w $74d1,$fffe
score_cop_50_hi: dc.w $00e4,0
score_cop_50_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $754b,$fffe
        else
        dc.w $753b,$fffe
        endif
score_cop_51_hi: dc.w $00e4,0
score_cop_51_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $75ab,$fffe
        else
        dc.w $759b,$fffe
        endif
score_cop_52_hi: dc.w $00e4,0
score_cop_52_lo: dc.w $00e6,0
        dc.w $75d1,$fffe
score_cop_53_hi: dc.w $00e4,0
score_cop_53_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $764b,$fffe
        else
        dc.w $763b,$fffe
        endif
score_cop_54_hi: dc.w $00e4,0
score_cop_54_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $76ab,$fffe
        else
        dc.w $769b,$fffe
        endif
score_cop_55_hi: dc.w $00e4,0
score_cop_55_lo: dc.w $00e6,0
        dc.w $76d1,$fffe
score_cop_56_hi: dc.w $00e4,0
score_cop_56_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $774b,$fffe
        else
        dc.w $773b,$fffe
        endif
score_cop_57_hi: dc.w $00e4,0
score_cop_57_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $77ab,$fffe
        else
        dc.w $779b,$fffe
        endif
score_cop_58_hi: dc.w $00e4,0
score_cop_58_lo: dc.w $00e6,0
        dc.w $77d1,$fffe
score_cop_59_hi: dc.w $00e4,0
score_cop_59_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $784b,$fffe
        else
        dc.w $783b,$fffe
        endif
score_cop_60_hi: dc.w $00e4,0
score_cop_60_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $78ab,$fffe
        else
        dc.w $789b,$fffe
        endif
score_cop_61_hi: dc.w $00e4,0
score_cop_61_lo: dc.w $00e6,0
        dc.w $78d1,$fffe
score_cop_62_hi: dc.w $00e4,0
score_cop_62_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $794b,$fffe
        else
        dc.w $793b,$fffe
        endif
score_cop_63_hi: dc.w $00e4,0
score_cop_63_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $79ab,$fffe
        else
        dc.w $799b,$fffe
        endif
score_cop_64_hi: dc.w $00e4,0
score_cop_64_lo: dc.w $00e6,0
        dc.w $79d1,$fffe
score_cop_65_hi: dc.w $00e4,0
score_cop_65_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7a4b,$fffe
        else
        dc.w $7a3b,$fffe
        endif
score_cop_66_hi: dc.w $00e4,0
score_cop_66_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7aab,$fffe
        else
        dc.w $7a9b,$fffe
        endif
score_cop_67_hi: dc.w $00e4,0
score_cop_67_lo: dc.w $00e6,0
        dc.w $7ad1,$fffe
score_cop_68_hi: dc.w $00e4,0
score_cop_68_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7b4b,$fffe
        else
        dc.w $7b3b,$fffe
        endif
score_cop_69_hi: dc.w $00e4,0
score_cop_69_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7bab,$fffe
        else
        dc.w $7b9b,$fffe
        endif
score_cop_70_hi: dc.w $00e4,0
score_cop_70_lo: dc.w $00e6,0
        dc.w $7bd1,$fffe
score_cop_71_hi: dc.w $00e4,0
score_cop_71_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7c4b,$fffe
        else
        dc.w $7c3b,$fffe
        endif
score_cop_72_hi: dc.w $00e4,0
score_cop_72_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7cab,$fffe
        else
        dc.w $7c9b,$fffe
        endif
score_cop_73_hi: dc.w $00e4,0
score_cop_73_lo: dc.w $00e6,0
        dc.w $7cd1,$fffe
score_cop_74_hi: dc.w $00e4,0
score_cop_74_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7d4b,$fffe
        else
        dc.w $7d3b,$fffe
        endif
score_cop_75_hi: dc.w $00e4,0
score_cop_75_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7dab,$fffe
        else
        dc.w $7d9b,$fffe
        endif
score_cop_76_hi: dc.w $00e4,0
score_cop_76_lo: dc.w $00e6,0
        dc.w $7dd1,$fffe
score_cop_77_hi: dc.w $00e4,0
score_cop_77_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7e4b,$fffe
        else
        dc.w $7e3b,$fffe
        endif
score_cop_78_hi: dc.w $00e4,0
score_cop_78_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7eab,$fffe
        else
        dc.w $7e9b,$fffe
        endif
score_cop_79_hi: dc.w $00e4,0
score_cop_79_lo: dc.w $00e6,0
        dc.w $7ed1,$fffe
score_cop_80_hi: dc.w $00e4,0
score_cop_80_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7f4b,$fffe
        else
        dc.w $7f3b,$fffe
        endif
score_cop_81_hi: dc.w $00e4,0
score_cop_81_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $7fab,$fffe
        else
        dc.w $7f9b,$fffe
        endif
score_cop_82_hi: dc.w $00e4,0
score_cop_82_lo: dc.w $00e6,0
        dc.w $7fd1,$fffe
score_cop_83_hi: dc.w $00e4,0
score_cop_83_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $804b,$fffe
        else
        dc.w $803b,$fffe
        endif
score_cop_84_hi: dc.w $00e4,0
score_cop_84_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $80ab,$fffe
        else
        dc.w $809b,$fffe
        endif
score_cop_85_hi: dc.w $00e4,0
score_cop_85_lo: dc.w $00e6,0
        dc.w $80d1,$fffe
score_cop_86_hi: dc.w $00e4,0
score_cop_86_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $814b,$fffe
        else
        dc.w $813b,$fffe
        endif
score_cop_87_hi: dc.w $00e4,0
score_cop_87_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $81ab,$fffe
        else
        dc.w $819b,$fffe
        endif
score_cop_88_hi: dc.w $00e4,0
score_cop_88_lo: dc.w $00e6,0
        dc.w $81d1,$fffe
score_cop_89_hi: dc.w $00e4,0
score_cop_89_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $824b,$fffe
        else
        dc.w $823b,$fffe
        endif
score_cop_90_hi: dc.w $00e4,0
score_cop_90_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $82ab,$fffe
        else
        dc.w $829b,$fffe
        endif
score_cop_91_hi: dc.w $00e4,0
score_cop_91_lo: dc.w $00e6,0
        dc.w $82d1,$fffe
score_cop_92_hi: dc.w $00e4,0
score_cop_92_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $834b,$fffe
        else
        dc.w $833b,$fffe
        endif
score_cop_93_hi: dc.w $00e4,0
score_cop_93_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $83ab,$fffe
        else
        dc.w $839b,$fffe
        endif
score_cop_94_hi: dc.w $00e4,0
score_cop_94_lo: dc.w $00e6,0
        dc.w $83d1,$fffe
score_cop_95_hi: dc.w $00e4,0
score_cop_95_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $844b,$fffe
        else
        dc.w $843b,$fffe
        endif
score_cop_96_hi: dc.w $00e4,0
score_cop_96_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $84ab,$fffe
        else
        dc.w $849b,$fffe
        endif
score_cop_97_hi: dc.w $00e4,0
score_cop_97_lo: dc.w $00e6,0
        dc.w $84d1,$fffe
score_cop_98_hi: dc.w $00e4,0
score_cop_98_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $854b,$fffe
        else
        dc.w $853b,$fffe
        endif
score_cop_99_hi: dc.w $00e4,0
score_cop_99_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $85ab,$fffe
        else
        dc.w $859b,$fffe
        endif
score_cop_100_hi: dc.w $00e4,0
score_cop_100_lo: dc.w $00e6,0
        dc.w $85d1,$fffe
score_cop_101_hi: dc.w $00e4,0
score_cop_101_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $864b,$fffe
        else
        dc.w $863b,$fffe
        endif
score_cop_102_hi: dc.w $00e4,0
score_cop_102_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $86ab,$fffe
        else
        dc.w $869b,$fffe
        endif
score_cop_103_hi: dc.w $00e4,0
score_cop_103_lo: dc.w $00e6,0
        dc.w $86d1,$fffe
score_cop_104_hi: dc.w $00e4,0
score_cop_104_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $874b,$fffe
        else
        dc.w $873b,$fffe
        endif
score_cop_105_hi: dc.w $00e4,0
score_cop_105_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $87ab,$fffe
        else
        dc.w $879b,$fffe
        endif
score_cop_106_hi: dc.w $00e4,0
score_cop_106_lo: dc.w $00e6,0
        dc.w $87d1,$fffe
score_cop_107_hi: dc.w $00e4,0
score_cop_107_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $884b,$fffe
        else
        dc.w $883b,$fffe
        endif
score_cop_108_hi: dc.w $00e4,0
score_cop_108_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $88ab,$fffe
        else
        dc.w $889b,$fffe
        endif
score_cop_109_hi: dc.w $00e4,0
score_cop_109_lo: dc.w $00e6,0
        dc.w $88d1,$fffe
score_cop_110_hi: dc.w $00e4,0
score_cop_110_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $894b,$fffe
        else
        dc.w $893b,$fffe
        endif
score_cop_111_hi: dc.w $00e4,0
score_cop_111_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $89ab,$fffe
        else
        dc.w $899b,$fffe
        endif
score_cop_112_hi: dc.w $00e4,0
score_cop_112_lo: dc.w $00e6,0
        dc.w $89d1,$fffe
score_cop_113_hi: dc.w $00e4,0
score_cop_113_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8a4b,$fffe
        else
        dc.w $8a3b,$fffe
        endif
score_cop_114_hi: dc.w $00e4,0
score_cop_114_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8aab,$fffe
        else
        dc.w $8a9b,$fffe
        endif
score_cop_115_hi: dc.w $00e4,0
score_cop_115_lo: dc.w $00e6,0
        dc.w $8ad1,$fffe
score_cop_116_hi: dc.w $00e4,0
score_cop_116_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8b4b,$fffe
        else
        dc.w $8b3b,$fffe
        endif
score_cop_117_hi: dc.w $00e4,0
score_cop_117_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8bab,$fffe
        else
        dc.w $8b9b,$fffe
        endif
score_cop_118_hi: dc.w $00e4,0
score_cop_118_lo: dc.w $00e6,0
        dc.w $8bd1,$fffe
score_cop_119_hi: dc.w $00e4,0
score_cop_119_lo: dc.w $00e6,0
        dc.w $8c01,$fffe
score_cop_120_hi: dc.w $00e0,0
score_cop_120_lo: dc.w $00e2,0
score_cop_121_hi: dc.w $00e4,0
score_cop_121_lo: dc.w $00e6,0
score_cop_122_hi: dc.w $00e8,0
score_cop_122_lo: dc.w $00ea,0
score_cop_123_hi: dc.w $00ec,0
score_cop_123_lo: dc.w $00ee,0
        ifd ENHANCED_INTERFACE
        dc.w $8c4b,$fffe
        else
        dc.w $8c3b,$fffe
        endif
score_cop_124_hi: dc.w $00e4,0
score_cop_124_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8c61,$fffe
        else
        dc.w $8c51,$fffe
        endif
score_cop_125_hi: dc.w $00e4,0
score_cop_125_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8cab,$fffe
        else
        dc.w $8c9b,$fffe
        endif
score_cop_126_hi: dc.w $00e4,0
score_cop_126_lo: dc.w $00e6,0
        dc.w $8cd1,$fffe
score_cop_127_hi: dc.w $00e4,0
score_cop_127_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8d4b,$fffe
        else
        dc.w $8d3b,$fffe
        endif
score_cop_128_hi: dc.w $00e4,0
score_cop_128_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8d61,$fffe
        else
        dc.w $8d51,$fffe
        endif
score_cop_129_hi: dc.w $00e4,0
score_cop_129_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8dab,$fffe
        else
        dc.w $8d9b,$fffe
        endif
score_cop_130_hi: dc.w $00e4,0
score_cop_130_lo: dc.w $00e6,0
        dc.w $8dd1,$fffe
score_cop_131_hi: dc.w $00e4,0
score_cop_131_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8e4b,$fffe
        else
        dc.w $8e3b,$fffe
        endif
score_cop_132_hi: dc.w $00e4,0
score_cop_132_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8e61,$fffe
        else
        dc.w $8e51,$fffe
        endif
score_cop_133_hi: dc.w $00e4,0
score_cop_133_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8eab,$fffe
        else
        dc.w $8e9b,$fffe
        endif
score_cop_134_hi: dc.w $00e4,0
score_cop_134_lo: dc.w $00e6,0
        dc.w $8ed1,$fffe
score_cop_135_hi: dc.w $00e4,0
score_cop_135_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8f4b,$fffe
        else
        dc.w $8f3b,$fffe
        endif
score_cop_136_hi: dc.w $00e4,0
score_cop_136_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8f61,$fffe
        else
        dc.w $8f51,$fffe
        endif
score_cop_137_hi: dc.w $00e4,0
score_cop_137_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $8fab,$fffe
        else
        dc.w $8f9b,$fffe
        endif
score_cop_138_hi: dc.w $00e4,0
score_cop_138_lo: dc.w $00e6,0
        dc.w $8fd1,$fffe
score_cop_139_hi: dc.w $00e4,0
score_cop_139_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $904b,$fffe
        else
        dc.w $903b,$fffe
        endif
score_cop_140_hi: dc.w $00e4,0
score_cop_140_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9061,$fffe
        else
        dc.w $9051,$fffe
        endif
score_cop_141_hi: dc.w $00e4,0
score_cop_141_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $90ab,$fffe
        else
        dc.w $909b,$fffe
        endif
score_cop_142_hi: dc.w $00e4,0
score_cop_142_lo: dc.w $00e6,0
        dc.w $90d1,$fffe
score_cop_143_hi: dc.w $00e4,0
score_cop_143_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $914b,$fffe
        else
        dc.w $913b,$fffe
        endif
score_cop_144_hi: dc.w $00e4,0
score_cop_144_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9161,$fffe
        else
        dc.w $9151,$fffe
        endif
score_cop_145_hi: dc.w $00e4,0
score_cop_145_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $91ab,$fffe
        else
        dc.w $919b,$fffe
        endif
score_cop_146_hi: dc.w $00e4,0
score_cop_146_lo: dc.w $00e6,0
        dc.w $91d1,$fffe
score_cop_147_hi: dc.w $00e4,0
score_cop_147_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $924b,$fffe
        else
        dc.w $923b,$fffe
        endif
score_cop_148_hi: dc.w $00e4,0
score_cop_148_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9261,$fffe
        else
        dc.w $9251,$fffe
        endif
score_cop_149_hi: dc.w $00e4,0
score_cop_149_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $92ab,$fffe
        else
        dc.w $929b,$fffe
        endif
score_cop_150_hi: dc.w $00e4,0
score_cop_150_lo: dc.w $00e6,0
        dc.w $92d1,$fffe
score_cop_151_hi: dc.w $00e4,0
score_cop_151_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $934b,$fffe
        else
        dc.w $933b,$fffe
        endif
score_cop_152_hi: dc.w $00e4,0
score_cop_152_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9361,$fffe
        else
        dc.w $9351,$fffe
        endif
score_cop_153_hi: dc.w $00e4,0
score_cop_153_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $93ab,$fffe
        else
        dc.w $939b,$fffe
        endif
score_cop_154_hi: dc.w $00e4,0
score_cop_154_lo: dc.w $00e6,0
        dc.w $93d1,$fffe
score_cop_155_hi: dc.w $00e4,0
score_cop_155_lo: dc.w $00e6,0
        dc.w $9401,$fffe
score_cop_156_hi: dc.w $00e0,0
score_cop_156_lo: dc.w $00e2,0
score_cop_157_hi: dc.w $00e4,0
score_cop_157_lo: dc.w $00e6,0
score_cop_158_hi: dc.w $00e8,0
score_cop_158_lo: dc.w $00ea,0
score_cop_159_hi: dc.w $00ec,0
score_cop_159_lo: dc.w $00ee,0
        ifd ENHANCED_INTERFACE
        dc.w $944b,$fffe
        else
        dc.w $943b,$fffe
        endif
score_cop_160_hi: dc.w $00e4,0
score_cop_160_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $94ab,$fffe
        else
        dc.w $949b,$fffe
        endif
score_cop_161_hi: dc.w $00e4,0
score_cop_161_lo: dc.w $00e6,0
        dc.w $94d1,$fffe
score_cop_162_hi: dc.w $00e4,0
score_cop_162_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $954b,$fffe
        else
        dc.w $953b,$fffe
        endif
score_cop_163_hi: dc.w $00e4,0
score_cop_163_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $95ab,$fffe
        else
        dc.w $959b,$fffe
        endif
score_cop_164_hi: dc.w $00e4,0
score_cop_164_lo: dc.w $00e6,0
        dc.w $95d1,$fffe
score_cop_165_hi: dc.w $00e4,0
score_cop_165_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $964b,$fffe
        else
        dc.w $963b,$fffe
        endif
score_cop_166_hi: dc.w $00e4,0
score_cop_166_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $96ab,$fffe
        else
        dc.w $969b,$fffe
        endif
score_cop_167_hi: dc.w $00e4,0
score_cop_167_lo: dc.w $00e6,0
        dc.w $96d1,$fffe
score_cop_168_hi: dc.w $00e4,0
score_cop_168_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $974b,$fffe
        else
        dc.w $973b,$fffe
        endif
score_cop_169_hi: dc.w $00e4,0
score_cop_169_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $97ab,$fffe
        else
        dc.w $979b,$fffe
        endif
score_cop_170_hi: dc.w $00e4,0
score_cop_170_lo: dc.w $00e6,0
        dc.w $97d1,$fffe
score_cop_171_hi: dc.w $00e4,0
score_cop_171_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $984b,$fffe
        else
        dc.w $983b,$fffe
        endif
score_cop_172_hi: dc.w $00e4,0
score_cop_172_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $98ab,$fffe
        else
        dc.w $989b,$fffe
        endif
score_cop_173_hi: dc.w $00e4,0
score_cop_173_lo: dc.w $00e6,0
        dc.w $98d1,$fffe
score_cop_174_hi: dc.w $00e4,0
score_cop_174_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $994b,$fffe
        else
        dc.w $993b,$fffe
        endif
score_cop_175_hi: dc.w $00e4,0
score_cop_175_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $99ab,$fffe
        else
        dc.w $999b,$fffe
        endif
score_cop_176_hi: dc.w $00e4,0
score_cop_176_lo: dc.w $00e6,0
        dc.w $99d1,$fffe
score_cop_177_hi: dc.w $00e4,0
score_cop_177_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9a4b,$fffe
        else
        dc.w $9a3b,$fffe
        endif
score_cop_178_hi: dc.w $00e4,0
score_cop_178_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9aab,$fffe
        else
        dc.w $9a9b,$fffe
        endif
score_cop_179_hi: dc.w $00e4,0
score_cop_179_lo: dc.w $00e6,0
        dc.w $9ad1,$fffe
score_cop_180_hi: dc.w $00e4,0
score_cop_180_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9b4b,$fffe
        else
        dc.w $9b3b,$fffe
        endif
score_cop_181_hi: dc.w $00e4,0
score_cop_181_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9bab,$fffe
        else
        dc.w $9b9b,$fffe
        endif
score_cop_182_hi: dc.w $00e4,0
score_cop_182_lo: dc.w $00e6,0
        dc.w $9bd1,$fffe
score_cop_183_hi: dc.w $00e4,0
score_cop_183_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9c4b,$fffe
        else
        dc.w $9c3b,$fffe
        endif
score_cop_184_hi: dc.w $00e4,0
score_cop_184_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9cab,$fffe
        else
        dc.w $9c9b,$fffe
        endif
score_cop_185_hi: dc.w $00e4,0
score_cop_185_lo: dc.w $00e6,0
        dc.w $9cd1,$fffe
score_cop_186_hi: dc.w $00e4,0
score_cop_186_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9d4b,$fffe
        else
        dc.w $9d3b,$fffe
        endif
score_cop_187_hi: dc.w $00e4,0
score_cop_187_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9dab,$fffe
        else
        dc.w $9d9b,$fffe
        endif
score_cop_188_hi: dc.w $00e4,0
score_cop_188_lo: dc.w $00e6,0
        dc.w $9dd1,$fffe
score_cop_189_hi: dc.w $00e4,0
score_cop_189_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9e4b,$fffe
        else
        dc.w $9e3b,$fffe
        endif
score_cop_190_hi: dc.w $00e4,0
score_cop_190_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9eab,$fffe
        else
        dc.w $9e9b,$fffe
        endif
score_cop_191_hi: dc.w $00e4,0
score_cop_191_lo: dc.w $00e6,0
        dc.w $9ed1,$fffe
score_cop_192_hi: dc.w $00e4,0
score_cop_192_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9f4b,$fffe
        else
        dc.w $9f3b,$fffe
        endif
score_cop_193_hi: dc.w $00e4,0
score_cop_193_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $9fab,$fffe
        else
        dc.w $9f9b,$fffe
        endif
score_cop_194_hi: dc.w $00e4,0
score_cop_194_lo: dc.w $00e6,0
        dc.w $9fd1,$fffe
score_cop_195_hi: dc.w $00e4,0
score_cop_195_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $a04b,$fffe
        else
        dc.w $a03b,$fffe
        endif
score_cop_196_hi: dc.w $00e4,0
score_cop_196_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $a0ab,$fffe
        else
        dc.w $a09b,$fffe
        endif
score_cop_197_hi: dc.w $00e4,0
score_cop_197_lo: dc.w $00e6,0
        dc.w $a0d1,$fffe
score_cop_198_hi: dc.w $00e4,0
score_cop_198_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $a14b,$fffe
        else
        dc.w $a13b,$fffe
        endif
score_cop_199_hi: dc.w $00e4,0
score_cop_199_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $a1ab,$fffe
        else
        dc.w $a19b,$fffe
        endif
score_cop_200_hi: dc.w $00e4,0
score_cop_200_lo: dc.w $00e6,0
        dc.w $a1d1,$fffe
score_cop_201_hi: dc.w $00e4,0
score_cop_201_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $a24b,$fffe
        else
        dc.w $a23b,$fffe
        endif
score_cop_202_hi: dc.w $00e4,0
score_cop_202_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $a2ab,$fffe
        else
        dc.w $a29b,$fffe
        endif
score_cop_203_hi: dc.w $00e4,0
score_cop_203_lo: dc.w $00e6,0
        dc.w $a2d1,$fffe
score_cop_204_hi: dc.w $00e4,0
score_cop_204_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $a34b,$fffe
        else
        dc.w $a33b,$fffe
        endif
score_cop_205_hi: dc.w $00e4,0
score_cop_205_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $a3ab,$fffe
        else
        dc.w $a39b,$fffe
        endif
score_cop_206_hi: dc.w $00e4,0
score_cop_206_lo: dc.w $00e6,0
        dc.w $a3d1,$fffe
score_cop_207_hi: dc.w $00e4,0
score_cop_207_lo: dc.w $00e6,0
        ifd ENHANCED_INTERFACE
        dc.w $bca9,$fffe
        else
        dc.w $bc99,$fffe
        endif
score_cop_208_hi: dc.w $00ec,0
score_cop_208_lo: dc.w $00ee,0
        dc.w $bcd1,$fffe
score_cop_209_hi: dc.w $00ec,0
score_cop_209_lo: dc.w $00ee,0
        ifd ENHANCED_INTERFACE
        dc.w $bda9,$fffe
        else
        dc.w $bd99,$fffe
        endif
score_cop_210_hi: dc.w $00ec,0
score_cop_210_lo: dc.w $00ee,0
        dc.w $bdd1,$fffe
score_cop_211_hi: dc.w $00ec,0
score_cop_211_lo: dc.w $00ee,0
        ifd ENHANCED_INTERFACE
        dc.w $bea9,$fffe
        else
        dc.w $be99,$fffe
        endif
score_cop_212_hi: dc.w $00ec,0
score_cop_212_lo: dc.w $00ee,0
        dc.w $bed1,$fffe
score_cop_213_hi: dc.w $00ec,0
score_cop_213_lo: dc.w $00ee,0
        ifd ENHANCED_INTERFACE
        dc.w $bfa9,$fffe
        else
        dc.w $bf99,$fffe
        endif
score_cop_214_hi: dc.w $00ec,0
score_cop_214_lo: dc.w $00ee,0
        dc.w $bfd1,$fffe
score_cop_215_hi: dc.w $00ec,0
score_cop_215_lo: dc.w $00ee,0
        ifd ENHANCED_INTERFACE
        dc.w $c0a9,$fffe
        else
        dc.w $c099,$fffe
        endif
score_cop_216_hi: dc.w $00ec,0
score_cop_216_lo: dc.w $00ee,0
        dc.w $c0d1,$fffe
score_cop_217_hi: dc.w $00ec,0
score_cop_217_lo: dc.w $00ee,0
        ifd ENHANCED_INTERFACE
        dc.w $c1a9,$fffe
        else
        dc.w $c199,$fffe
        endif
score_cop_218_hi: dc.w $00ec,0
score_cop_218_lo: dc.w $00ee,0
        dc.w $c1d1,$fffe
score_cop_219_hi: dc.w $00ec,0
score_cop_219_lo: dc.w $00ee,0
        ifd ENHANCED_INTERFACE
        dc.w $c2a9,$fffe
        else
        dc.w $c299,$fffe
        endif
score_cop_220_hi: dc.w $00ec,0
score_cop_220_lo: dc.w $00ee,0
        dc.w $c2d1,$fffe
score_cop_221_hi: dc.w $00ec,0
score_cop_221_lo: dc.w $00ee,0
        ifd ENHANCED_INTERFACE
        dc.w $c3a9,$fffe
        else
        dc.w $c399,$fffe
        endif
score_cop_222_hi: dc.w $00ec,0
score_cop_222_lo: dc.w $00ee,0
        dc.w $c3d1,$fffe
score_cop_223_hi: dc.w $00ec,0
score_cop_223_lo: dc.w $00ee,0
