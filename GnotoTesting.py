from opentrons import protocol_api

# metadata
metadata = {
	'protocolName': 'Gnotobiotics 16S qPCR Testing', 
	'author': 'J Bisanz, jordan.bisanz@gmail.com',
	'description': 'Protocol for qPCR testing for bacterial contamination in germ-free mice via qPCR for total 16S rRNA copies. Does Zymo mag washes and loads 16S rRNA qPCR assay. Note: Assumes 16 sample. Etraction volumes have been scaled by a factor of 5 to reduce reagent use and speed up extraction',
	'apiLevel': '2.7'
}

def run(protocol: protocol_api.ProtocolContext):

	# which steps should be run?
	AddBindingBuffer = True
	AddBeads = True
	CaptureBinding = True
	Wash1 = True
	Wash2 = True
	LoadPlate = True
	MakeSTD = True
	LoadSTD = True
	Dry = True
	Elute = True
	AddTemplate = True


	# set tweakable variables
	cols_to_extract = [1,2] # which columns should be extracted should be extracted?
	set_rail_lights = True
	
	volume_magbeads = 5 # volume of mag beads (25ul originally)
	volume_bindingbuffer = 120 # binding buffer (600 originally)
	volume_wb1 = 180 # volume of wash buffer 1
	volume_wb2 = 180 # volume of wash buffer 2
	volume_h20 = 50 # volume of water
	volume_elution = 40 # elution volume to transfer to clean wells (defaults)
	
	capture_depth = 0 # depth below ideal bottom of plate to remove supernatants
	capture_min = 2 # number of minutes to capture beads on magnets
	nmix = 5 # number of times to pipette to mix
	drying_min = 0.5 # number of extra minutes to dry DNA after STD is made
	trash_speed = 1 # the relative speed to discard of liquids into trash, this is an integer multiplier of normal speed, set higher to clear bubbles on outside of tip
	elution_speed = 0.2 # relative speed to lift supernatant off beads

	# define deck layout
	MagModule = protocol.load_module('magnetic module gen2', 10)
	BindingPlate = MagModule.load_labware('biorad_96_wellplate_200ul_pcr') # use the full skirted biorad plate and make sure your samples are in the first 2 columns. Sample volume should be 40ul
	Solutions = protocol.load_labware('nest_12_reservoir_15ml', 7) # A1 200ul beads, A2 2.4mL binding buffer, A3 3.6mL WB1, A4 7.2mL WB2, A5 10mL H2O, A6 450ul mastermix + 90ul 10x primer solution
	qPCR = protocol.load_labware('biorad384pcrplate_384_wellplate_40ul', 1) # skirted 384 well plate for qPCR
	waste = protocol.load_labware('agilent_1_reservoir_290ml', 11)
	waste = waste['A1'].top(0)
	std = protocol.load_labware("opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", 2) #a 1.5mL eppendorf containing the 16S standard in A1
	
	#define tips
	tips_p200_1 = protocol.load_labware('opentrons_96_filtertiprack_200ul', 5)
	tips_p200_2 = protocol.load_labware('opentrons_96_filtertiprack_200ul', 8)
	tips_p20 = protocol.load_labware('opentrons_96_filtertiprack_20ul', 6)


	# define pipettes
	p300 = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tips_p200_1, tips_p200_2])
	p20 = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tips_p20])

	### Prerun setup ########################################
	MagModule.disengage()

	if AddBindingBuffer:
		protocol.comment('--------->Adding binding buffer')
		for i in cols_to_extract:
			p300.pick_up_tip()
			p300.aspirate(volume_bindingbuffer, Solutions['A2'])
			p300.dispense(volume_bindingbuffer, BindingPlate['A'+str(i)])
			p300.mix(nmix, volume_bindingbuffer*0.5, BindingPlate['A'+str(i)])
			p300.drop_tip()
		
	if AddBeads:
		protocol.comment('--------->Adding mag beads')
		p300.pick_up_tip()
		p300.mix(10, 30, Solutions['A1'])
		p300.drop_tip()
		
		for i in cols_to_extract:
			p20.pick_up_tip()
			#p20.mix(5, 20, Solutions['A1'])
			p20.aspirate(volume_magbeads, Solutions['A1'])
			p20.dispense(volume_magbeads, BindingPlate['A'+str(i)])
			p20.mix(nmix, 20)
			p20.drop_tip()
		
	if CaptureBinding:
		protocol.comment('--------->Removing Binding Buffer')
		MagModule.engage()
		protocol.delay(minutes=capture_min)
		for i in cols_to_extract:
			p300.pick_up_tip()
			p300.aspirate(200, BindingPlate['A'+str(i)].bottom(capture_depth), rate=elution_speed)
			p300.dispense(200, waste, rate = trash_speed)
			p300.drop_tip()

	if Wash1:
		protocol.comment('--------->Doing Wash 1')
		MagModule.disengage()
		for i in cols_to_extract:
			p300.pick_up_tip()
			p300.aspirate(volume_wb1, Solutions['A3'])
			p300.dispense(volume_wb1, BindingPlate['A'+str(i)])
			p300.mix(nmix, volume_wb1*0.5, BindingPlate['A'+str(i)])
			p300.drop_tip()
		MagModule.engage()
		protocol.delay(minutes=capture_min)
		for i in cols_to_extract:
			p300.pick_up_tip()
			p300.aspirate(200, BindingPlate['A'+str(i)].bottom(capture_depth), rate=elution_speed)
			p300.dispense(200, waste, rate = trash_speed)
			p300.drop_tip()

	if Wash2:
		for r in [1,2]:
			protocol.comment('--------->Doing Wash 2')
			MagModule.disengage()
			for i in cols_to_extract:
				p300.pick_up_tip()
				p300.aspirate(volume_wb2, Solutions['A4'])
				p300.dispense(volume_wb2, BindingPlate['A'+str(i)])
				p300.mix(nmix, volume_wb2*0.5, BindingPlate['A'+str(i)])
				p300.drop_tip()
			MagModule.engage()
			protocol.delay(minutes=capture_min)
			for i in cols_to_extract:
				p300.pick_up_tip()
				p300.aspirate(200, BindingPlate['A'+str(i)].bottom(capture_depth), rate=elution_speed)
				p300.dispense(200, waste, rate = trash_speed)
				p300.drop_tip()

	if LoadPlate:
		p20.pick_up_tip()
		for i in [1,2,3,4,5,6,22,23,24]:
			p20.aspirate(6, Solutions['A6'])
			p20.dispense(6, qPCR['A'+str(i)])
		p20.drop_tip()

	if MakeSTD:
		p300.pick_up_tip()
		p300.aspirate(90, Solutions['A5'])
		p300.dispense(90, BindingPlate['A10'])
		#p300.blow_out() #creates problematic air pockets for standard curve
		p300.drop_tip()
		
		p20.pick_up_tip(tips_p20['H12'])
		p20.aspirate(10, std['A1'].bottom(5))
		p20.dispense(10, BindingPlate['A10'])
		p20.mix(5,20,  BindingPlate['A10'])
		p20.drop_tip()
		
		#serial dilute from A10 down column
		ROWS = ['A','B','C','D','E','F','G']
		TIPS = ['G12','F12','E12','D12','C12','B12']
		for i in [0,1,2,3,4,5]:
			p20.pick_up_tip(tips_p20[TIPS[i]])
			p20.aspirate(10, BindingPlate[ROWS[i]+str(10)])
			p20.dispense(10, BindingPlate[ROWS[i+1]+str(10)])
			p20.mix(5,20, BindingPlate[ROWS[i+1]+str(10)].bottom(3))
			p20.mix(5,20, BindingPlate[ROWS[i+1]+str(10)].bottom(6))
			p20.mix(5,20, BindingPlate[ROWS[i+1]+str(10)].bottom(1))
			p20.mix(5,20, BindingPlate[ROWS[i+1]+str(10)].bottom(6))
			p20.drop_tip()
		
	if LoadSTD:
		p20.pick_up_tip()
		p20.aspirate(14, BindingPlate['A10'])
		p20.dispense(4, qPCR['A22'])
		p20.dispense(4, qPCR['A23'])
		p20.dispense(4, qPCR['A24'])
		p20.drop_tip()

	if Dry:
		protocol.comment('--------->Doing extra drying of DNA')
		protocol.delay(minutes=drying_min)

	if Elute:
		protocol.comment('--------->Eluting DNA')
		MagModule.disengage()
		for i in cols_to_extract:
			p300.pick_up_tip()
			p300.aspirate(volume_h20, Solutions['A5'])
			p300.dispense(volume_h20, BindingPlate['A'+str(i)])
			p300.mix(nmix, volume_h20*0.5, BindingPlate['A'+str(i)])
			p300.drop_tip()
		MagModule.engage()
		protocol.delay(minutes=capture_min)
		for i in [1,2]:
			p300.pick_up_tip()
			p300.aspirate(volume_elution, BindingPlate['A'+str(i)].bottom(capture_depth), rate=elution_speed)
			p300.dispense(volume_elution, BindingPlate['A'+str(i+10)])
			p300.drop_tip()

	if AddTemplate:
		p20.pick_up_tip()
		p20.aspirate(15, BindingPlate['A11'])
		p20.dispense(4, qPCR['A1'])
		p20.dispense(4, qPCR['A2'])
		p20.dispense(4, qPCR['A3'])
		p20.drop_tip()
		p20.pick_up_tip()
		p20.aspirate(15, BindingPlate['A12'])
		p20.dispense(4, qPCR['A4'])
		p20.dispense(4, qPCR['A5'])
		p20.dispense(4, qPCR['A6'])
		p20.drop_tip()
