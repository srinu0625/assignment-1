using UnityEngine;

public class Vehicle : MonoBehaviour
{
    [Header("Vehicle Settings")]
    public float motorForce = 2000f;
    public float steerAngle = 30f;
    public float brakeForce = 3000f;
    public float maxSpeed = 40f; // m/s roughly
    
    [Header("Wheel Colliders")]
    public WheelCollider frontLeft;
    public WheelCollider frontRight;
    public WheelCollider rearLeft;
    public WheelCollider rearRight;
    
    [System.NonSerialized] public bool occupied = false;
    [System.NonSerialized] public PlayerController driver;
    
    private Rigidbody rb;
    private float currentSteer;
    private float currentMotor;
    private bool braking;
    
    void Start()
    {
        rb = GetComponent<Rigidbody>();
        rb.centerOfMass = new Vector3(0, -0.5f, 0);
    }
    
    public void ProcessInput(float horizontal, float vertical, bool brake)
    {
        currentSteer = horizontal * steerAngle;
        currentMotor = vertical * motorForce;
        braking = brake;
    }
    
    void FixedUpdate()
    {
        if (!occupied) 
        {
            // Auto-brake when no driver
            frontLeft.brakeTorque = 100f;
            frontRight.brakeTorque = 100f;
            rearLeft.brakeTorque = 100f;
            rearRight.brakeTorque = 100f;
            return;
        }
        
        // Speed limit check
        if (rb.velocity.magnitude > maxSpeed && currentMotor > 0)
        {
            currentMotor = 0;
        }
        
        // Motor
        rearLeft.motorTorque = currentMotor;
        rearRight.motorTorque = currentMotor;
        
        // Steering
        frontLeft.steerAngle = currentSteer;
        frontRight.steerAngle = currentSteer;
        
        // Braking
        float brake = braking ? brakeForce : 0;
        frontLeft.brakeTorque = brake;
        frontRight.brakeTorque = brake;
        rearLeft.brakeTorque = brake;
        rearRight.brakeTorque = brake;
        
        // Anti-roll (simple stabilization)
        Vector3 localVelocity = transform.InverseTransformDirection(rb.velocity);
        if (Mathf.Abs(localVelocity.x) > 5f)
        {
            rb.AddForce(-transform.right * localVelocity.x * 100f);
        }
    }
    
    void Update()
    {
        // Update wheel meshes if you have visual wheels
        UpdateWheelPose(frontLeft);
        UpdateWheelPose(frontRight);
        UpdateWheelPose(rearLeft);
        UpdateWheelPose(rearRight);
    }
    
    void UpdateWheelPose(WheelCollider collider)
    {
        if (collider.transform.childCount == 0) return;
        
        Transform visualWheel = collider.transform.GetChild(0);
        Vector3 pos;
        Quaternion rot;
        collider.GetWorldPose(out pos, out rot);
        visualWheel.position = pos;
        visualWheel.rotation = rot;
    }
    
    void OnCollisionEnter(Collision collision)
    {
        // Damage to other objects/people
        if (collision.relativeVelocity.magnitude > 10f)
        {
            EnemyAI enemy = collision.gameObject.GetComponent<EnemyAI>();
            if (enemy != null)
            {
                enemy.TakeDamage(50f);
            }
            
            // Wanted level for hitting people
            if (collision.gameObject.CompareTag("Enemy") || collision.gameObject.CompareTag("Civilian"))
            {
                GTAGameManager.Instance.AddWantedLevel(1);
            }
        }
    }
}
